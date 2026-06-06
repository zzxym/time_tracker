/** Tag management component with create/edit/delete. */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import { useTagStore } from '../../stores/tagStore';
import { DEFAULT_COLORS } from '@time-tracker/shared';
import ConfirmDialog from '../common/ConfirmDialog';

const TagManager: React.FC = () => {
  const { tags, createTag, updateTag, deleteTag } = useTagStore();
  const [showForm, setShowForm] = useState(false);
  const [editingTag, setEditingTag] = useState<{ id: string; name: string; color: string } | null>(null);
  const [tagName, setTagName] = useState('');
  const [tagColor, setTagColor] = useState(DEFAULT_COLORS[0]);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleOpenCreate = () => {
    setEditingTag(null);
    setTagName('');
    setTagColor(DEFAULT_COLORS[0]);
    setShowForm(true);
  };

  const handleOpenEdit = (tag: { id: string; name: string; color: string }) => {
    setEditingTag(tag);
    setTagName(tag.name);
    setTagColor(tag.color);
    setShowForm(true);
  };

  const handleSubmit = async () => {
    if (!tagName.trim()) return;
    setIsSubmitting(true);
    try {
      if (editingTag) {
        await updateTag(editingTag.id, { name: tagName.trim(), color: tagColor });
      } else {
        await createTag({ name: tagName.trim(), color: tagColor });
      }
      setShowForm(false);
    } catch (error) {
      console.error('Failed to save tag:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (tagId: string) => {
    setConfirmDelete(null);
    try {
      await deleteTag(tagId);
    } catch (error) {
      console.error('Failed to delete tag:', error);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Manage Tags</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenCreate}>
          New Tag
        </Button>
      </Box>

      {tags.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">
            No tags yet. Create one to categorize your activities!
          </Typography>
        </Box>
      ) : (
        <List>
          {tags.map((tag) => (
            <ListItem
              key={tag.id}
              sx={{
                borderBottom: '1px solid',
                borderColor: 'divider',
              }}
            >
              <Box
                sx={{
                  width: 20,
                  height: 20,
                  borderRadius: '50%',
                  backgroundColor: tag.color,
                  mr: 2,
                  flexShrink: 0,
                }}
              />
              <ListItemText primary={tag.name} />
              <ListItemSecondaryAction>
                <IconButton
                  size="small"
                  onClick={() => handleOpenEdit({ id: tag.id, name: tag.name, color: tag.color })}
                >
                  <EditIcon fontSize="small" />
                </IconButton>
                <IconButton
                  size="small"
                  onClick={() => setConfirmDelete(tag.id)}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}

      {/* Tag form dialog */}
      <Dialog open={showForm} onClose={() => setShowForm(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingTag ? 'Edit Tag' : 'Create Tag'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Tag Name"
              value={tagName}
              onChange={(e) => setTagName(e.target.value)}
              fullWidth
              autoFocus
              required
            />
            <Box>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                Color
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {DEFAULT_COLORS.map((c) => (
                  <Box
                    key={c}
                    onClick={() => setTagColor(c)}
                    sx={{
                      width: 28,
                      height: 28,
                      borderRadius: '50%',
                      backgroundColor: c,
                      cursor: 'pointer',
                      border: tagColor === c ? '3px solid #333' : '2px solid transparent',
                    }}
                  />
                ))}
              </Box>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowForm(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={!tagName.trim() || isSubmitting}
          >
            {editingTag ? 'Save' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={Boolean(confirmDelete)}
        title="Delete Tag"
        message="Are you sure you want to delete this tag? It will be removed from all associated activities."
        onConfirm={() => confirmDelete && handleDelete(confirmDelete)}
        onCancel={() => setConfirmDelete(null)}
        severity="error"
      />
    </Box>
  );
};

export default TagManager;
