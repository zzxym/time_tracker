/** Tag filter component for activity filtering. */

import React from 'react';
import { Box, Typography, Checkbox, FormControlLabel } from '@mui/material';
import { useTagStore } from '../../stores/tagStore';

const TagFilter: React.FC = () => {
  const { tags, selectedTagIds, toggleTagFilter, clearTagFilters } = useTagStore();

  if (tags.length === 0) return null;

  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Typography variant="subtitle2" color="text.secondary">
          Filter by Tags
        </Typography>
        {selectedTagIds.length > 0 && (
          <Typography
            variant="caption"
            color="primary"
            sx={{ cursor: 'pointer' }}
            onClick={clearTagFilters}
          >
            Clear all
          </Typography>
        )}
      </Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
        {tags.map((tag) => (
          <FormControlLabel
            key={tag.id}
            control={
              <Checkbox
                checked={selectedTagIds.includes(tag.id)}
                onChange={() => toggleTagFilter(tag.id)}
                size="small"
                sx={{ color: tag.color, '&.Mui-checked': { color: tag.color } }}
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <Box
                  sx={{
                    width: 10,
                    height: 10,
                    borderRadius: '50%',
                    backgroundColor: tag.color,
                  }}
                />
                <Typography variant="body2">{tag.name}</Typography>
              </Box>
            }
          />
        ))}
      </Box>
    </Box>
  );
};

export default TagFilter;
