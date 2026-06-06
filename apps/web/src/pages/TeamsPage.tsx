/** Teams list page. */

import React, { useEffect, useState } from 'react';
import {
  Box, Card, CardContent, Typography, Button, List, ListItem,
  ListItemText, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Alert, CircularProgress, Tooltip,
} from '@mui/material';
import { Add, Group, Delete, Edit, Visibility } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTeamStore } from '../../stores/teamStore';

export default function TeamsPage() {
  const navigate = useNavigate();
  const { teams, loading, error, fetchTeams, deleteTeam } = useTeamStore();
  const [createOpen, setCreateOpen] = useState(false);
  const [delTarget, setDelTarget] = useState<string | null>(null);

  useEffect(() => { fetchTeams(); }, []);

  return (
    <Box sx={{ p: 3, maxWidth: 900, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">我的团队</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setCreateOpen(true)}>
          创建团队
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => useTeamStore.getState().clearError()}>{error}</Alert>}
      {loading && <CircularProgress />}
      {!loading && teams.length === 0 && (
        <Typography color="text.secondary" align="center" sx={{ mt: 4 }}>
          暂无团队，点击"创建团队"开始
        </Typography>
      )}

      {/* Team List */}
      <List>
        {teams.map((t) => (
          <Card key={t.id} sx={{ mb: 2 }}>
            <CardContent>
              <ListItem
                secondaryAction={
                  <Box>
                    <Tooltip title="查看详情">
                      <IconButton onClick={() => navigate(`/teams/${t.id}`)}>
                        <Visibility />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="删除">
                      <IconButton color="error" onClick={() => setDelTarget(t.id)}>
                        <Delete />
                      </IconButton>
                    </Tooltip>
                  </Box>
                }
              >
                <ListItemText
                  primary={t.name}
                  secondary={`${t.description || '暂无描述'} · ${t.member_count} 名成员 · 创建于 ${new Date(t.created_at).toLocaleDateString('zh-CN')}`}
                />
              </ListItem>
            </CardContent>
          </Card>
        ))}
      </List>

      {/* Create Dialog */}
      <CreateTeamDialog open={createOpen} onClose={() => setCreateOpen(false)} />

      {/* Delete Confirm */}
      <ConfirmDialog
        open={!!delTarget}
        title="删除团队"
        content="确定要删除此团队吗？此操作不可恢复。"
        onConfirm={async () => { if (delTarget) { await deleteTeam(delTarget); setDelTarget(null); } }}
        onCancel={() => setDelTarget(null)}
      />
    </Box>
  );
}

// ── Create Team Dialog ─────────────────────────────────────

function CreateTeamDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const createTeam = useTeamStore((s) => s.createTeam);

  const handleSubmit = async () => {
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      await createTeam(name.trim(), desc.trim());
      setName(''); setDesc(''); onClose();
    } catch { /* error shown via store */ } finally { setSubmitting(false); }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>创建团队</DialogTitle>
      <DialogContent sx={{ mt: 1 }}>
        <TextField
          fullWidth label="团队名称" value={name} onChange={(e) => setName(e.target.value)}
          sx={{ mb: 2 }} autoFocus
        />
        <TextField
          fullWidth label="团队描述（可选）" value={desc} onChange={(e) => setDesc(e.target.value)}
          multiline rows={3}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button variant="contained" onClick={handleSubmit} disabled={!name.trim() || submitting}>
          {submitting ? '创建中...' : '创建'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

// ── Confirm Dialog (reusable) ─────────────────────────────

function ConfirmDialog({ open, title, content, onConfirm, onCancel }: {
  open: boolean; title: string; content: string;
  onConfirm: () => Promise<void> | void; onCancel: () => void;
}) {
  const [loading, setLoading] = useState(false);
  const handleConfirm = async () => { setLoading(true); try { await onConfirm(); } finally { setLoading(false); } };
  return (
    <Dialog open={open} onClose={onCancel}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent><Typography>{content}</Typography></DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>取消</Button>
        <Button color="error" onClick={handleConfirm} disabled={loading}>
          {loading ? '处理中...' : '确认'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
