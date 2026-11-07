void VulkanReplayConsumerBase::ProcessInitImageCommand(format::HandleId             device_id,
                                                       format::HandleId             image_id,
                                                       uint64_t                     data_size,
                                                       uint32_t                     aspect,
                                                       uint32_t                     layout,
                                                       const std::vector<uint64_t>& level_sizes,
                                                       const uint8_t*               data)
{
    VulkanDeviceInfo* device_info = object_info_table_->GetVkDeviceInfo(device_id);
    VulkanImageInfo*  image_info  = object_info_table_->GetVkImageInfo(image_id);

    if ((device_info != nullptr) && (image_info != nullptr))
    {
        VkResult                   result      = VK_SUCCESS;
        VkDevice                   device      = device_info->handle;
        VkImage                    image       = image_info->handle;
        VulkanResourceInitializer* initializer = device_info->resource_initializer.get();

        assert((device != VK_NULL_HANDLE) && (image != VK_NULL_HANDLE));

        if (initializer != nullptr)
        {
            std::vector<VkBufferImageCopy> copy_regions;

            if (data_size > 0)
            {
                if ((image_info->tiling == VK_IMAGE_TILING_LINEAR) &&
                    (image_info->memory_property_flags &
                     (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_CACHED_BIT)) ==
                        (VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_CACHED_BIT))
                {
                    result = initializer->LoadData(data_size, data, image_info->allocator_data);

                    if (result != VK_SUCCESS)
                    {
                        GFXRECON_LOG_WARNING(
                            "State snapshot mapped memory copy failed for VkImage object (ID = %" PRIu64
                            ", handle = 0x%" PRIx64 ")",
                            image_id,
                            image);
                    }
                }
                else
                {
                    // Create one copy region per mip-level.
                    VkBufferImageCopy copy_region;
                    copy_region.bufferRowLength                 = 0; // Request tightly packed data.
                    copy_region.bufferImageHeight               = 0; // Request tightly packed data.
                    copy_region.bufferOffset                    = 0;
                    copy_region.imageOffset.x                   = 0;
                    copy_region.imageOffset.y                   = 0;
                    copy_region.imageOffset.z                   = 0;
                    copy_region.imageSubresource.aspectMask     = aspect;
                    copy_region.imageSubresource.baseArrayLayer = 0;
                    copy_region.imageSubresource.layerCount     = image_info->layer_count;

                    const VkDeviceSize copy_alignment =
                        graphics::GetBufferImageCopyOffsetAlignment(image_info->format, aspect);
                    VkDeviceSize current_offset = 0;
                    VkDeviceSize required_size  = 0;

                    assert(image_info->level_count == level_sizes.size());

                    for (uint32_t i = 0; i < image_info->level_count; ++i)
                    {
                        copy_region.imageSubresource.mipLevel = i;
                        copy_region.imageExtent.width         = std::max(1u, (image_info->extent.width >> i));
                        copy_region.imageExtent.height        = std::max(1u, (image_info->extent.height >> i));
                        copy_region.imageExtent.depth         = std::max(1u, (image_info->extent.depth >> i));

                        // Keep per-mip offsets valid even when level_sizes are tightly packed or
                        // use non-power-of-two format alignments.
                        //
                        // For backward compatibility with older captures, this may be switched to
                        // contiguous (legacy) offsets below when aligned offsets would exceed payload size.
                        current_offset           = graphics::AlignBufferOffset(current_offset, copy_alignment);
                        copy_region.bufferOffset = current_offset;

                        copy_regions.push_back(copy_region);
                        required_size = std::max(required_size, current_offset + level_sizes[i]);
                        current_offset += level_sizes[i];
                    }

