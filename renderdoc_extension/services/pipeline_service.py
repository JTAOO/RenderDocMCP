"""
Pipeline state service for RenderDoc.
"""

import base64

from ..renderdoc_compat import rd

from ..utils import Parsers, Serializers, Helpers


class RenderDocAPICompat:
    """
    RenderDoc API compatibility layer for handling differences between versions.

    RenderDoc 1.17 uses:
    - GetConstantBuffer() returning BoundCBuffer (resourceId, byteOffset, byteSize, inlineData)
    - GetReadOnlyResources/GetReadWriteResources returning List[BoundResourceArray]
    - BoundResourceArray has bindPoint and resources[] list

    RenderDoc 1.43 uses:
    - GetConstantBlock() returning UsedDescriptor (access, descriptor, sampler)
    - GetReadOnlyResources/GetReadWriteResources returning List[UsedDescriptor]
    - UsedDescriptor has access.index and descriptor.resource
    """

    @staticmethod
    def get_constant_buffer(pipe, stage, index, array_idx=0):
        """Get constant buffer binding with API compatibility."""
        bind = None
        if hasattr(pipe, 'GetConstantBlock'):
            bind = pipe.GetConstantBlock(stage, index, array_idx)
        elif hasattr(pipe, 'GetConstantBuffer'):
            bind = pipe.GetConstantBuffer(stage, index, array_idx)

        if not bind:
            return None

        # Normalize to common format
        result = {'resource_id': None, 'byte_offset': 0, 'byte_size': 0}

        if hasattr(bind, 'descriptor') and hasattr(bind.descriptor, 'resource'):
            # RenderDoc 1.43+ (UsedDescriptor)
            result['resource_id'] = bind.descriptor.resource
            result['byte_offset'] = getattr(bind.descriptor, 'byteOffset', 0)
            result['byte_size'] = getattr(bind.descriptor, 'byteSize', 0)
        elif hasattr(bind, 'resourceId'):
            # RenderDoc 1.17 (BoundCBuffer)
            result['resource_id'] = bind.resourceId
            result['byte_offset'] = getattr(bind, 'byteOffset', 0)
            result['byte_size'] = getattr(bind, 'byteSize', 0)

        return result

    @staticmethod
    def get_shader_resources(pipe, stage, only_used=False):
        """
        Get shader resources with API compatibility.

        Returns list of dicts with normalized keys:
        - slot: bind slot index
        - resource_id: the bound resource ID
        - first_mip, num_mips, first_slice, num_slices: texture subresource info
        """
        resources = []

        # Try GetReadOnlyResources first
        if hasattr(pipe, 'GetReadOnlyResources'):
            raw_resources = pipe.GetReadOnlyResources(stage, only_used)
        else:
            return resources

        for item in raw_resources:
            # RenderDoc 1.43+: UsedDescriptor with access and descriptor
            if hasattr(item, 'descriptor') and hasattr(item, 'access'):
                if item.descriptor.resource == rd.ResourceId.Null():
                    continue
                resources.append({
                    'slot': getattr(item.access, 'index', 0),
                    'resource_id': item.descriptor.resource,
                    'first_mip': getattr(item.descriptor, 'firstMip', 0),
                    'num_mips': getattr(item.descriptor, 'numMips', 0),
                    'first_slice': getattr(item.descriptor, 'firstSlice', 0),
                    'num_slices': getattr(item.descriptor, 'numSlices', 0),
                })
            # RenderDoc 1.17: BoundResourceArray with bindPoint and resources list
            elif hasattr(item, 'bindPoint') and hasattr(item, 'resources'):
                slot = getattr(item.bindPoint, 'index', 0) if hasattr(item.bindPoint, 'index') else 0
                for res in item.resources:
                    if hasattr(res, 'resourceId') and res.resourceId != rd.ResourceId.Null():
                        resources.append({
                            'slot': slot,
                            'resource_id': res.resourceId,
                            'first_mip': getattr(res, 'firstMip', -1),
                            'num_mips': getattr(res, 'numMips', -1),
                            'first_slice': getattr(res, 'firstSlice', -1),
                            'num_slices': getattr(res, 'numSlices', -1),
                        })
            # Fallback: try direct descriptor access
            elif hasattr(item, 'descriptor'):
                if item.descriptor.resource == rd.ResourceId.Null():
                    continue
                resources.append({
                    'slot': getattr(item, 'slot', 0),
                    'resource_id': item.descriptor.resource,
                    'first_mip': getattr(item.descriptor, 'firstMip', 0),
                    'num_mips': getattr(item.descriptor, 'numMips', 0),
                    'first_slice': getattr(item.descriptor, 'firstSlice', 0),
                    'num_slices': getattr(item.descriptor, 'numSlices', 0),
                })

        return resources

    @staticmethod
    def get_shader_uavs(pipe, stage, only_used=False):
        """
        Get shader UAVs (read-write resources) with API compatibility.

        Returns list of dicts with normalized keys:
        - slot: bind slot index
        - resource_id: the bound resource ID
        - first_element, num_elements: UAV range info
        """
        uavs = []

        if hasattr(pipe, 'GetReadWriteResources'):
            raw_uavs = pipe.GetReadWriteResources(stage, only_used)
        else:
            return uavs

        for item in raw_uavs:
            # RenderDoc 1.43+: UsedDescriptor
            if hasattr(item, 'descriptor') and hasattr(item, 'access'):
                if item.descriptor.resource == rd.ResourceId.Null():
                    continue
                uavs.append({
                    'slot': getattr(item.access, 'index', 0),
                    'resource_id': item.descriptor.resource,
                    'first_element': getattr(item.descriptor, 'firstMip', 0),
                    'num_elements': getattr(item.descriptor, 'numMips', 0),
                })
            # RenderDoc 1.17: BoundResourceArray
            elif hasattr(item, 'bindPoint') and hasattr(item, 'resources'):
                slot = getattr(item.bindPoint, 'index', 0) if hasattr(item.bindPoint, 'index') else 0
                for res in item.resources:
                    if hasattr(res, 'resourceId') and res.resourceId != rd.ResourceId.Null():
                        uavs.append({
                            'slot': slot,
                            'resource_id': res.resourceId,
                            'first_element': getattr(res, 'firstMip', -1),
                            'num_elements': getattr(res, 'numMips', -1),
                        })
            elif hasattr(item, 'descriptor'):
                if item.descriptor.resource == rd.ResourceId.Null():
                    continue
                uavs.append({
                    'slot': getattr(item, 'slot', 0),
                    'resource_id': item.descriptor.resource,
                    'first_element': getattr(item.descriptor, 'firstMip', 0),
                    'num_elements': getattr(item.descriptor, 'numMips', 0),
                })

        return uavs

    @staticmethod
    def get_shader_samplers(pipe, stage):
        """
        Get shader samplers with API compatibility.

        Returns list of dicts with normalized sampler info.
        """
        samplers = []

        if hasattr(pipe, 'GetSamplers'):
            raw_samplers = pipe.GetSamplers(stage)
        else:
            return samplers

        for item in raw_samplers:
            # RenderDoc 1.43+: UsedDescriptor
            if hasattr(item, 'access') and hasattr(item, 'sampler'):
                samp_info = {'slot': getattr(item.access, 'index', 0)}
                if hasattr(item, 'sampler'):
                    samp_info['sampler_descriptor'] = item.sampler
                samplers.append(samp_info)
            # RenderDoc 1.17: BoundResourceArray
            elif hasattr(item, 'bindPoint') and hasattr(item, 'resources'):
                slot = getattr(item.bindPoint, 'index', 0) if hasattr(item.bindPoint, 'index') else 0
                for res in item.resources:
                    if hasattr(res, 'resourceId') and res.resourceId != rd.ResourceId.Null():
                        samplers.append({
                            'slot': slot,
                            'resource_id': res.resourceId,
                        })
            elif hasattr(item, 'descriptor'):
                samplers.append({
                    'slot': getattr(item, 'slot', 0),
                    'descriptor': item.descriptor,
                })

        return samplers


class PipelineService:
    """Pipeline state service"""

    def __init__(self, ctx, invoke_fn):
        self.ctx = ctx
        self._invoke = invoke_fn

    def get_shader_info(self, event_id, stage):
        """Get shader information for a specific stage"""
        if not self.ctx.IsCaptureLoaded():
            raise ValueError("No capture loaded")

        result = {"shader": None, "error": None}

        def callback(controller):
            controller.SetFrameEvent(event_id, True)

            pipe = controller.GetPipelineState()
            stage_enum = Parsers.parse_stage(stage)

            shader = pipe.GetShader(stage_enum)
            if shader == rd.ResourceId.Null():
                result["error"] = "No %s shader bound" % stage
                return

            entry = pipe.GetShaderEntryPoint(stage_enum)
            reflection = pipe.GetShaderReflection(stage_enum)

            shader_info = {
                "resource_id": str(shader),
                "entry_point": entry,
                "stage": stage,
            }

            # Get raw shader bytecode (DXBC/DXIL)
            if reflection:
                # Convert bytes to base64 string for JSON serialization
                shader_info["raw_bytes_base64"] = base64.b64encode(reflection.rawBytes).decode('ascii')
                shader_info["raw_bytes_size"] = len(reflection.rawBytes)
                shader_info["encoding"] = str(reflection.encoding)  # "DXBC" or "DXIL"

            # Get disassembly
            try:
                targets = controller.GetDisassemblyTargets(True)
                if targets:
                    disasm = controller.DisassembleShader(
                        pipe.GetGraphicsPipelineObject(), reflection, targets[0]
                    )
                    shader_info["disassembly"] = disasm
            except Exception as e:
                shader_info["disassembly_error"] = str(e)

            # Get constant buffer info
            if reflection:
                shader_info["constant_buffers"] = self._get_cbuffer_info(
                    controller, pipe, reflection, stage_enum
                )
                shader_info["resources"] = self._get_resource_bindings(reflection)

            result["shader"] = shader_info

        self._invoke(callback)

        if result["error"]:
            raise ValueError(result["error"])
        return result["shader"]

    def get_pipeline_state(self, event_id):
        """Get full pipeline state at an event"""
        if not self.ctx.IsCaptureLoaded():
            raise ValueError("No capture loaded")

        result = {"pipeline": None, "error": None}

        def callback(controller):
            controller.SetFrameEvent(event_id, True)

            pipe = controller.GetPipelineState()
            api = controller.GetAPIProperties().pipelineType

            pipeline_info = {
                "event_id": event_id,
                "api": str(api),
            }

            # Shader stages with detailed bindings
            stages = {}
            stage_list = Helpers.get_all_shader_stages()
            for stage in stage_list:
                shader = pipe.GetShader(stage)
                if shader != rd.ResourceId.Null():
                    stage_info = {
                        "resource_id": str(shader),
                        "entry_point": pipe.GetShaderEntryPoint(stage),
                    }

                    reflection = pipe.GetShaderReflection(stage)

                    stage_info["resources"] = self._get_stage_resources(
                        controller, pipe, stage, reflection
                    )
                    stage_info["uavs"] = self._get_stage_uavs(
                        controller, pipe, stage, reflection
                    )
                    stage_info["samplers"] = self._get_stage_samplers(
                        pipe, stage, reflection
                    )
                    stage_info["constant_buffers"] = self._get_stage_cbuffers(
                        controller, pipe, stage, reflection
                    )

                    stages[str(stage)] = stage_info

            pipeline_info["shaders"] = stages

            # Viewport and scissor
            try:
                vp_scissor = pipe.GetViewportScissor()
                if vp_scissor:
                    viewports = []
                    for v in vp_scissor.viewports:
                        viewports.append(
                            {
                                "x": v.x,
                                "y": v.y,
                                "width": v.width,
                                "height": v.height,
                                "min_depth": v.minDepth,
                                "max_depth": v.maxDepth,
                            }
                        )
                    pipeline_info["viewports"] = viewports
            except Exception:
                pass

            # Render targets
            try:
                om = pipe.GetOutputMerger()
                if om:
                    rts = []
                    for i, rt in enumerate(om.renderTargets):
                        if rt.resourceId != rd.ResourceId.Null():
                            rts.append({"index": i, "resource_id": str(rt.resourceId)})
                    pipeline_info["render_targets"] = rts

                    if om.depthTarget.resourceId != rd.ResourceId.Null():
                        pipeline_info["depth_target"] = str(om.depthTarget.resourceId)
            except Exception:
                pass

            # Input assembly
            try:
                ia = pipe.GetIAState()
                if ia:
                    pipeline_info["input_assembly"] = {"topology": str(ia.topology)}
            except Exception:
                pass

            result["pipeline"] = pipeline_info

        self._invoke(callback)

        if result["error"]:
            raise ValueError(result["error"])
        return result["pipeline"]

    def _get_stage_resources(self, controller, pipe, stage, reflection):
        """Get shader resource views (SRVs) for a stage"""
        resources = []
        try:
            srvs = RenderDocAPICompat.get_shader_resources(pipe, stage, False)

            name_map = {}
            if reflection:
                for res in reflection.readOnlyResources:
                    name_map[res.fixedBindNumber] = res.name

            for srv in srvs:
                if srv['resource_id'] == rd.ResourceId.Null():
                    continue

                res_info = {
                    "slot": srv['slot'],
                    "name": name_map.get(srv['slot'], ""),
                    "resource_id": str(srv['resource_id']),
                }

                res_info.update(
                    self._get_resource_details(controller, srv['resource_id'])
                )

                res_info["first_mip"] = srv['first_mip']
                res_info["num_mips"] = srv['num_mips']
                res_info["first_slice"] = srv['first_slice']
                res_info["num_slices"] = srv['num_slices']

                resources.append(res_info)
        except Exception as e:
            resources.append({"error": str(e)})

        return resources

    def _get_stage_uavs(self, controller, pipe, stage, reflection):
        """Get unordered access views (UAVs) for a stage"""
        uavs = []
        try:
            uav_list = RenderDocAPICompat.get_shader_uavs(pipe, stage, False)

            name_map = {}
            if reflection:
                for res in reflection.readWriteResources:
                    name_map[res.fixedBindNumber] = res.name

            for uav in uav_list:
                if uav['resource_id'] == rd.ResourceId.Null():
                    continue

                slot = uav['slot']
                uav_info = {
                    "slot": slot,
                    "name": name_map.get(slot, ""),
                    "resource_id": str(uav['resource_id']),
                }

                uav_info.update(
                    self._get_resource_details(controller, uav['resource_id'])
                )

                uav_info["first_element"] = uav['first_element']
                uav_info["num_elements"] = uav['num_elements']

                uavs.append(uav_info)
        except Exception as e:
            uavs.append({"error": str(e)})

        return uavs

    def _get_stage_samplers(self, pipe, stage, reflection):
        """Get samplers for a stage"""
        samplers = []
        try:
            sampler_list = RenderDocAPICompat.get_shader_samplers(pipe, stage)

            name_map = {}
            if reflection:
                for samp in reflection.samplers:
                    name_map[samp.fixedBindNumber] = samp.name

            for samp in sampler_list:
                slot = samp.get('slot', 0)
                samp_info = {
                    "slot": slot,
                    "name": name_map.get(slot, ""),
                }

                # Handle different sampler descriptor types
                desc = samp.get('descriptor') or samp.get('sampler_descriptor')
                if desc:
                    try:
                        samp_info["address_u"] = str(desc.addressU)
                        samp_info["address_v"] = str(desc.addressV)
                        samp_info["address_w"] = str(desc.addressW)
                    except AttributeError:
                        pass

                    try:
                        samp_info["filter"] = str(desc.filter)
                    except AttributeError:
                        pass

                    try:
                        samp_info["max_anisotropy"] = desc.maxAnisotropy
                    except AttributeError:
                        pass

                    try:
                        samp_info["min_lod"] = desc.minLOD
                        samp_info["max_lod"] = desc.maxLOD
                        samp_info["mip_lod_bias"] = desc.mipLODBias
                    except AttributeError:
                        pass

                    try:
                        samp_info["border_color"] = [
                            desc.borderColor[0],
                            desc.borderColor[1],
                            desc.borderColor[2],
                            desc.borderColor[3],
                        ]
                    except (AttributeError, TypeError):
                        pass

                try:
                    samp_info["compare_function"] = str(desc.compareFunction)
                except AttributeError:
                    pass

                samplers.append(samp_info)
        except Exception as e:
            samplers.append({"error": str(e)})

        return samplers

    def _get_stage_cbuffers(self, controller, pipe, stage, reflection):
        """Get constant buffers for a stage from shader reflection"""
        cbuffers = []
        try:
            if not reflection:
                return cbuffers

            for cb in reflection.constantBlocks:
                slot = cb.bindPoint if hasattr(cb, 'bindPoint') else cb.fixedBindNumber
                cb_info = {
                    "slot": slot,
                    "name": cb.name,
                    "byte_size": cb.byteSize,
                    "variable_count": len(cb.variables) if cb.variables else 0,
                    "variables": [],
                }
                if cb.variables:
                    for var in cb.variables:
                        cb_info["variables"].append({
                            "name": var.name,
                            "byte_offset": var.byteOffset,
                            "type": str(var.type.name) if var.type else "",
                        })
                cbuffers.append(cb_info)

        except Exception as e:
            cbuffers.append({"error": str(e)})

        return cbuffers

    def _get_cbuffer_info(self, controller, pipe, reflection, stage):
        """Get constant buffer information and values"""
        cbuffers = []

        for i, cb in enumerate(reflection.constantBlocks):
            cb_info = {
                "name": cb.name,
                "slot": i,
                "size": cb.byteSize,
                "variables": [],
            }

            try:
                # API compatibility: GetConstantBlock (1.43) vs GetConstantBuffer (1.17)
                bind = None
                if hasattr(pipe, 'GetConstantBlock'):
                    bind = pipe.GetConstantBlock(stage, i, 0)
                elif hasattr(pipe, 'GetConstantBuffer'):
                    bind = pipe.GetConstantBuffer(stage, i, 0)

                if bind:
                    # API compatibility: UsedDescriptor (1.43) vs BoundCBuffer (1.17)
                    # 1.43: bind.descriptor.resource
                    # 1.17: bind.resourceId
                    buffer_resource_id = None
                    byte_offset = 0
                    byte_size = 0

                    if hasattr(bind, 'descriptor') and hasattr(bind.descriptor, 'resource'):
                        # RenderDoc 1.43+ (UsedDescriptor)
                        buffer_resource_id = bind.descriptor.resource
                        byte_offset = getattr(bind.descriptor, 'byteOffset', 0)
                        byte_size = getattr(bind.descriptor, 'byteSize', 0)
                    elif hasattr(bind, 'resourceId'):
                        # RenderDoc 1.17 (BoundCBuffer)
                        buffer_resource_id = bind.resourceId
                        byte_offset = getattr(bind, 'byteOffset', 0)
                        byte_size = getattr(bind, 'byteSize', 0)

                    if buffer_resource_id and buffer_resource_id != rd.ResourceId.Null():
                        variables = controller.GetCBufferVariableContents(
                            pipe.GetGraphicsPipelineObject(),
                            reflection.resourceId,
                            stage,
                            reflection.entryPoint,
                            i,
                            buffer_resource_id,
                            byte_offset,
                            byte_size,
                        )
                        cb_info["variables"] = Serializers.serialize_variables(variables)
            except Exception as e:
                cb_info["error"] = str(e)

            cbuffers.append(cb_info)

        return cbuffers

    def _get_resource_details(self, controller, resource_id):
        """Get details about a resource (texture or buffer)"""
        details = {}

        try:
            resource_name = self.ctx.GetResourceName(resource_id)
            if resource_name:
                details["resource_name"] = resource_name
        except Exception:
            pass

        for tex in controller.GetTextures():
            if tex.resourceId == resource_id:
                details["type"] = "texture"
                details["width"] = tex.width
                details["height"] = tex.height
                details["depth"] = tex.depth
                details["array_size"] = tex.arraysize
                details["mip_levels"] = tex.mips
                details["format"] = str(tex.format.Name())
                details["dimension"] = str(tex.type)
                details["msaa_samples"] = tex.msSamp
                return details

        for buf in controller.GetBuffers():
            if buf.resourceId == resource_id:
                details["type"] = "buffer"
                details["length"] = buf.length
                return details

        return details

    def get_cbuffer_contents(self, event_id, stage):
        """Get constant buffer contents for a specific stage at an event"""
        if not self.ctx.IsCaptureLoaded():
            raise ValueError("No capture loaded")

        result = {"cbuffers": [], "error": None}

        def callback(controller):
            controller.SetFrameEvent(event_id, True)

            pipe = controller.GetPipelineState()
            stage_enum = Parsers.parse_stage(stage)

            reflection = pipe.GetShaderReflection(stage_enum)
            if not reflection:
                result["error"] = "No shader reflection available for %s stage" % stage
                return

            cbuffers = []
            for i, cb in enumerate(reflection.constantBlocks):
                cb_info = {
                    "name": cb.name,
                    "slot": i,
                    "byte_size": cb.byteSize,
                    "variables": [],
                }

                try:
                    # API compatibility: GetConstantBlock (1.43) vs GetConstantBuffer (1.17)
                    bind = None
                    if hasattr(pipe, 'GetConstantBlock'):
                        bind = pipe.GetConstantBlock(stage_enum, i, 0)
                    elif hasattr(pipe, 'GetConstantBuffer'):
                        bind = pipe.GetConstantBuffer(stage_enum, i, 0)

                    if bind:
                        # API compatibility: UsedDescriptor (1.43) vs BoundCBuffer (1.17)
                        # 1.43: bind.descriptor.resource
                        # 1.17: bind.resourceId
                        buffer_resource_id = None
                        byte_offset = 0
                        byte_size = 0

                        if hasattr(bind, 'descriptor') and hasattr(bind.descriptor, 'resource'):
                            # RenderDoc 1.43+ (UsedDescriptor)
                            buffer_resource_id = bind.descriptor.resource
                            byte_offset = getattr(bind.descriptor, 'byteOffset', 0)
                            byte_size = getattr(bind.descriptor, 'byteSize', 0)
                        elif hasattr(bind, 'resourceId'):
                            # RenderDoc 1.17 (BoundCBuffer)
                            buffer_resource_id = bind.resourceId
                            byte_offset = getattr(bind, 'byteOffset', 0)
                            byte_size = getattr(bind, 'byteSize', 0)

                        if buffer_resource_id and buffer_resource_id != rd.ResourceId.Null():
                            variables = controller.GetCBufferVariableContents(
                                pipe.GetGraphicsPipelineObject(),
                                reflection.resourceId,
                                stage_enum,
                                reflection.entryPoint,
                                i,
                                buffer_resource_id,
                                byte_offset,
                                byte_size,
                            )
                            cb_info["variables"] = Serializers.serialize_variables(variables)
                        else:
                            cb_info["note"] = "Constant buffer not bound"
                    else:
                        cb_info["note"] = "Constant buffer binding not available"
                except Exception as e:
                    cb_info["error"] = str(e)

                cbuffers.append(cb_info)

            result["cbuffers"] = cbuffers

        self._invoke(callback)

        if result["error"]:
            raise ValueError(result["error"])
        return result

    def _get_resource_bindings(self, reflection):
        """Get shader resource bindings"""
        resources = []

        try:
            for res in reflection.readOnlyResources:
                resources.append(
                    {
                        "name": res.name,
                        "type": str(res.resType),
                        "binding": res.fixedBindNumber,
                        "access": "ReadOnly",
                    }
                )
        except Exception:
            pass

        try:
            for res in reflection.readWriteResources:
                resources.append(
                    {
                        "name": res.name,
                        "type": str(res.resType),
                        "binding": res.fixedBindNumber,
                        "access": "ReadWrite",
                    }
                )
        except Exception:
            pass

        return resources
