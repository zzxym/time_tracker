/** Activity create/edit form dialog. */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Box,
  Typography,
  FormControlLabel,
  Checkbox,
  Chip,
} from '@mui/material';
import type { Activity } from '@time-tracker/shared';
import { useActivityStore } from '../../stores/activityStore';
import { useTagStore } from '../../stores/tagStore';
import { DEFAULT_COLORS } from '@time-tracker/shared';

interface ActivityFormProps {
  open: boolean;
  onClose: () => void;
  activity?: Activity | null;
}

const ActivityForm: React.FC<ActivityFormProps> = ({ open, onClose, activity }) => {
  const [name, setName] = useState('');
  const [color, setColor] = useState<string>(DEFAULT_COLORS[0]);
  const [isParallel, setIsParallel] = useState(false);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { createActivity, updateActivity } = useActivityStore();
  const { tags } = useTagStore();

  const isEditing = Boolean(activity);

  useEffect(() => {
    if (activity) {
      setName(activity.name);
      setColor(activity.color);
      setIsParallel(activity.is_parallel);
      setSelectedTagIds(activity.tags?.map((t) => t.id) || []);
    } else {
      setName('');
      setColor(DEFAULT_COLORS[0]);
      setIsParallel(false);
      setSelectedTagIds([]);
    }
  }, [activity, open]);

  const handleSubmit = async () => {
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      if (isEditing && activity) {
        await updateActivity(activity.id, {
          name: name.trim(),
          color,
          is_parallel: isParallel,
          tag_ids: selectedTagIds,
        });
      } else {
        await createActivity({
          name: name.trim(),
          color,
          is_parallel: isParallel,
          tag_ids: selectedTagIds,
        });
      }
      onClose();
    } catch (error) {
      console.error('Failed to save activity:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const toggleTag = (tagId: string) => {
    setSelectedTagIds((prev) =>
      prev.includes(tagId)
        ? prev.filter((id) => id !== tagId)
        : [...prev, tagId]
    );
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        {isEditing ? '编辑活动' : '创建活动'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
          <TextField
            label="活动名称"
            value={name}
            onChange={(e) => setName(e.target.value)}
            fullWidth
            autoFocus
            required
            placeholder="例如：阅读、编程、运动"
          />

          {/* Color picker */}
          <Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              颜色
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {DEFAULT_COLORS.map((c) => (
                <Box
                  key={c}
                  onClick={() => setColor(c)}
                  sx={{
                    width: 32,
                    height: 32,
                    borderRadius: '50%',
                    backgroundColor: c,
                    cursor: 'pointer',
                    border: color === c ? '3px solid #333' : '2px solid transparent',
                    transition: 'border 0.2s',
                  }}
                />
              ))}
            </Box>
          </Box>

          {/* Parallel mode */}
          <FormControlLabel
            control={
              <Checkbox
                checked={isParallel}
                onChange={(e) => setIsParallel(e.target.checked)}
              />
            }
            label="允许并行执行（与其他活动同时运行）"
          />

          {/* Tag selection */}
          {tags.length > 0 && (
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Tags
              </Typography>
              <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                {tags.map((tag) => (
                  <Chip
                    key={tag.id}
                    label={tag.name}
                    onClick={() => toggleTag(tag.id)}
                    variant={selectedTagIds.includes(tag.id) ? 'filled' : 'outlined'}
                    sx={{
                      backgroundColor: selectedTagIds.includes(tag.id) ? tag.color : 'transparent',
                      color: selectedTagIds.includes(tag.id) ? 'white' : tag.color,
                      borderColor: tag.color,
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!name.trim() || isSubmitting}
        >
          {isEditing ? '保存' : '创建'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ActivityForm;
