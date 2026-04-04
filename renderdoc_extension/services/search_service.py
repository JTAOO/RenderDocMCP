"""
Reverse lookup search service for RenderDoc.
"""

import renderdoc as rd

from ..utils import Parsers, Helpers


class SearchService:
    """Reverse lookup search service"""

    def __init__(self, ctx, invoke_fn):
        self.ctx = ctx
        self._invoke = invoke_fn

    def _search_draws(self, matcher_fn, max_scans=500, offset=0):
        """
        Common template for searching draw calls with pagination.

        Args:
            matcher_fn: Function(pipe, controller, action, ctx) -> match_reason or None
            max_scans: Maximum number of draws to scan (default 500 for performance)
            offset: Starting offset for pagination (default 0)
        """
        if not self.ctx.IsCaptureLoaded():
            raise ValueError("No capture loaded")

        result = {"matches": [], "scanned_draws": 0, "offset": offset, "total_draws": None}

        # Capture parameters for callback
        params = {"offset": offset, "max_scans": max_scans}

        def callback(controller):
            root_actions = controller.GetRootActions()
            structured_file = controller.GetStructuredFile()
            all_actions = Helpers.flatten_actions(root_actions)

            # Filter to only draw calls and dispatches
            draw_actions = [
                a for a in all_actions
                if a.flags & (rd.ActionFlags.Drawcall | rd.ActionFlags.Dispatch)
            ]

            total_draws = len(draw_actions)
            result["total_draws"] = total_draws

            # Apply offset and limit using captured params
            start_idx = min(params["offset"], max(0, total_draws - 1)) if params["offset"] > 0 else 0
            end_idx = min(start_idx + params["max_scans"], total_draws)
            draw_actions_to_scan = draw_actions[start_idx:end_idx]

            scan_count = len(draw_actions_to_scan)
            result["scanned_draws"] = scan_count
            result["offset"] = start_idx

            # Scan only the specified range
            for action in draw_actions_to_scan:
                controller.SetFrameEvent(action.eventId, False)
                pipe = controller.GetPipelineState()

                match_reason = matcher_fn(pipe, controller, action, self.ctx)
                if match_reason:
                    result["matches"].append({
                        "event_id": action.eventId,
                        "name": action.GetName(structured_file),
                        "match_reason": match_reason,
                    })

        self._invoke(callback)
        result["total_matches_in_range"] = len(result["matches"])

        # Pagination info
        has_more = (result["offset"] + params["max_scans"]) < result.get("total_draws", 0)
        result["has_more"] = has_more
        result["next_offset"] = (result["offset"] + params["max_scans"]) if has_more else None

        return result

    def find_draws_by_shader(self, shader_name, stage=None, offset=0, max_scans=500):
        """Find all draw calls using a shader with the given name (partial match).

        Args:
            shader_name: Shader name to search for (partial match, empty string matches all)
            stage: Optional shader stage to filter (vertex, hull, domain, geometry, pixel, compute)
            offset: Starting offset for pagination (default 0)
            max_scans: Maximum number of draws to scan (default 500)
        """
        # Determine which stages to check
        if stage:
            stages_to_check = [Parsers.parse_stage(stage)]
        else:
            stages_to_check = Helpers.get_all_shader_stages()

        def matcher(pipe, controller, action, ctx):
            for s in stages_to_check:
                shader = pipe.GetShader(s)
                if shader == rd.ResourceId.Null():
                    continue

                reflection = pipe.GetShaderReflection(s)
                if reflection:
                    entry_point = pipe.GetShaderEntryPoint(s)
                    shader_debug_name = ""
                    try:
                        shader_debug_name = ctx.GetResourceName(shader)
                    except Exception:
                        pass

                    if shader_name and shader_name.lower() in entry_point.lower():
                        return "%s entry_point: '%s'" % (str(s), entry_point)
                    elif shader_debug_name and shader_name and shader_name.lower() in shader_debug_name.lower():
                        return "%s name: '%s'" % (str(s), shader_debug_name)
                    elif shader_name == "" or shader_name is None:
                        # Empty search: return all draws with shaders
                        return "%s entry_point: '%s'" % (str(s), entry_point)
            return None

        return self._search_draws(matcher, max_scans, offset)

    def find_draws_by_texture(self, texture_name, offset=0, max_scans=500):
        """Find all draw calls using a texture with the given name (partial match).

        Args:
            texture_name: Texture name to search for (partial match, empty string matches all)
            offset: Starting offset for pagination (default 0)
            max_scans: Maximum number of draws to scan (default 500)
        """
        # Handle empty texture name - return draws with any texture bindings
        empty_search = not texture_name or texture_name == ""

        def matcher(pipe, controller, action, ctx):
            stages_to_check = Helpers.get_all_shader_stages()

            # Check SRVs (read-only resources)
            for stage in stages_to_check:
                try:
                    srvs = pipe.GetReadOnlyResources(stage, False)
                    for srv in srvs:
                        if srv.descriptor.resource == rd.ResourceId.Null():
                            continue
                        res_name = ""
                        try:
                            res_name = ctx.GetResourceName(srv.descriptor.resource)
                        except Exception:
                            pass
                        if empty_search or (res_name and texture_name.lower() in res_name.lower()):
                            return "%s SRV: '%s'" % (str(stage), res_name or str(srv.descriptor.resource))
                except Exception:
                    pass

                # Check UAVs (read-write resources)
                try:
                    uavs = pipe.GetReadWriteResources(stage, False)
                    for uav in uavs:
                        if uav.descriptor.resource == rd.ResourceId.Null():
                            continue
                        res_name = ""
                        try:
                            res_name = ctx.GetResourceName(uav.descriptor.resource)
                        except Exception:
                            pass
                        if empty_search or (res_name and texture_name.lower() in res_name.lower()):
                            return "%s UAV: '%s'" % (str(stage), res_name or str(uav.descriptor.resource))
                except Exception:
                    pass

            # Check render targets
            try:
                om = pipe.GetOutputMerger()
                if om:
                    for i, rt in enumerate(om.renderTargets):
                        if rt.resourceId != rd.ResourceId.Null():
                            res_name = ""
                            try:
                                res_name = ctx.GetResourceName(rt.resourceId)
                            except Exception:
                                pass
                            if empty_search or (res_name and texture_name.lower() in res_name.lower()):
                                return "RenderTarget[%d]: '%s'" % (i, res_name or str(rt.resourceId))
            except Exception:
                pass

            return None

        return self._search_draws(matcher, max_scans, offset)

    def find_draws_by_resource(self, resource_id, offset=0, max_scans=500):
        """Find all draw calls using a specific resource ID (exact match).

        Args:
            resource_id: Resource ID to search for (exact match)
            offset: Starting offset for pagination (default 0)
            max_scans: Maximum number of draws to scan (default 500)
        """
        target_rid = Parsers.parse_resource_id(resource_id)
        stages_to_check = Helpers.get_all_shader_stages()

        def matcher(pipe, controller, action, ctx):
            # Check shaders
            for stage in stages_to_check:
                shader = pipe.GetShader(stage)
                if shader == target_rid:
                    return "%s shader" % str(stage)

            # Check SRVs and UAVs
            for stage in stages_to_check:
                try:
                    srvs = pipe.GetReadOnlyResources(stage, False)
                    for srv in srvs:
                        if srv.descriptor.resource == target_rid:
                            return "%s SRV slot %d" % (str(stage), srv.access.index)
                except Exception:
                    pass

                try:
                    uavs = pipe.GetReadWriteResources(stage, False)
                    for uav in uavs:
                        if uav.descriptor.resource == target_rid:
                            return "%s UAV slot %d" % (str(stage), uav.access.index)
                except Exception:
                    pass

            # Check render targets
            try:
                om = pipe.GetOutputMerger()
                if om:
                    for i, rt in enumerate(om.renderTargets):
                        if rt.resourceId == target_rid:
                            return "RenderTarget[%d]" % i
                    if om.depthTarget.resourceId == target_rid:
                        return "DepthTarget"
            except Exception:
                pass

            return None

        return self._search_draws(matcher, max_scans, offset)
