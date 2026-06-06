/** Team detail page — members, status, activities, stats. */

import React, { useEffect, useState } from 'react';
import {
  Box, Card, CardContent, Typography, Button, List, ListItem,
  ListItemText, IconButton, Chip, Alert, CircularProgress,
  Tab, Tabs, TextField, Dialog, DialogTitle, DialogContent,
  DialogActions, Select, MenuItem, FormControl, InputLabel,
  Table, TableBody, TableCell, TableHead, TableRow, Paper,
  Tooltip, LinearProgress,
} from '@mui/material';
import { Add, Delete, Refresh, BarChart, Group, Schedule } from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { useTeamStore } from '../../stores/teamStore';
import { getTeamActivities, getTeamStats } from '../../api/teams';
import type { TeamMemberStatus, TeamActivityResponse, TeamStats } from '../../types/team';
import ConfirmDialog from '../../components/common/ConfirmDialog';

// ── Helpers ──────────────────────────────────────────────

function fmtDuration(sec: number) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  return h > 0 ? `${h}时${m}分${s}秒` : `${m}分${s}秒`;
}

// ── Page ─────────────────────────────────────────────────

export default function TeamDetailPage() {
  const { teamId } = useParams<{ teamId: string }>();
  const navigate = useNavigate();
  const {
    currentTeam, members, memberStatuses, loading, error,
    fetchTeamDetail, fetchMemberStatus, clearError,
    updateTeam, removeMember,
  } = useTeamStore();

  const [tab, setTab] = useState(0);
  const [activities, setActivities] = useState<TeamActivityResponse[]>([]);
  const [stats, setStats] = useState<TeamStats | null>(null);
  const [delMember, setDelMember] = useState<string | null>(null);
  const [editOpen, setEditOpen] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDesc, setEditDesc] = useState('');

  useEffect(() => {
    if (teamId) {
      fetchTeamDetail(teamId);
      fetchMemberStatus(teamId);
      // Poll status every 10s
      const timer = setInterval(() => fetchMemberStatus(teamId), 10000);
      return () => clearInterval(timer);
    }
  }, [teamId]);

  const loadActivities = async () => {
    if (!teamId) return;
    try {
      const data = await getTeamActivities(teamId);
      setActivities(data);
    } catch { /* ignore */ }
  };

  const loadStats = async () => {
    if (!teamId) return;
    try {
      const data = await getTeamStats();
      setStats(data);
    } catch { /* ignore */ }
  };

  useEffect(() => {
    if (tab === 2) loadActivities();
    if (tab === 3) loadStats();
  }, [tab]);

  if (loading && !currentTeam) {
    return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 8 }}><CircularProgress /></Box>;
  }
  if (!currentTeam) {
    return <Typography>团队不存在或无权访问</Typography>;
  }

  return (
    <Box sx={{ p: 3, maxWidth: 1100, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4">{currentTeam.name}</Typography>
          <Typography color="text.secondary">{currentTeam.description || '暂无描述'}</Typography>
          <Typography variant="caption" color="text.secondary">
            所有者：{currentTeam.owner_username} · {currentTeam.member_count} 名成员
          </Typography>
        </Box>
        <Box>
          <Button startIcon={<Refresh />} onClick={() => { fetchTeamDetail(teamId); fetchMemberStatus(teamId); }}>
            刷新
          </Button>
          <Button sx={{ ml: 1 }} onClick={() => { setEditName(currentTeam.name); setEditDesc(currentTeam.description); setEditOpen(true); }}>
            编辑
          </Button>
          <Button sx={{ ml: 1 }} onClick={() => navigate('/teams')}>返回列表</Button>
        </Box>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={clearError}>{error}</Alert>}

      {/* Tabs */}
      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
        <Tab icon={<Group />} label="成员状态" />
        <Tab icon={<Group />} label="成员管理" />
        <Tab icon={<Schedule />} label="活动记录" />
        <Tab icon={<BarChart />} label="统计报表" />
      </Tabs>

      {/* Tab 0: Member Status */}
      {tab === 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>成员实时状态</Typography>
          {memberStatuses.length === 0 && <Typography color="text.secondary">暂无成员状态</Typography>}
          {memberStatuses.map((ms) => (
            <Card key={ms.user_id} sx={{ mb: 2, p: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="subtitle1">{ms.username}</Typography>
                  {ms.current_activity ? (
                    <Box>
                      <Chip label={ms.current_activity_status === 'RUNNING' ? '进行中' : ms.current_activity_status} color="success" size="small" sx={{ mr: 1 }} />
                      <Typography component="span">{ms.current_activity}</Typography>
                      {ms.current_activity_started_at && (
                        <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                          开始于 {new Date(ms.current_activity_started_at).toLocaleTimeString('zh-CN')}
                        </Typography>
                      )}
                    </Box>
                  ) : (
                    <Typography color="text.secondary">当前空闲</Typography>
                  )}
                </Box>
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="h6">{fmtDuration(ms.today_duration_seconds)}</Typography>
                  <Typography variant="caption" color="text.secondary">今日时长</Typography>
                </Box>
              </Box>
            </Card>
          ))}
        </Paper>
      )}

      {/* Tab 1: Member Management */}
      {tab === 1 && (
        <MemberManagement teamId={teamId} members={members} onRefresh={() => fetchTeamDetail(teamId)} />
      )}

      {/* Tab 2: Activities */}
      {tab === 2 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>团队活动记录</Typography>
          {activities.length === 0 && <Typography color="text.secondary">暂无活动记录</Typography>}
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>成员</TableCell>
                <TableCell>活动名称</TableCell>
                <TableCell>状态</TableCell>
                <TableCell>开始时间</TableCell>
                <TableCell>时长</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {activities.map((a) => (
                <TableRow key={a.activity_id}>
                  <TableCell>{a.username}</TableCell>
                  <TableCell>{a.activity_name}</TableCell>
                  <TableCell>
                    <Chip label={a.activity_status === 'RUNNING' ? '进行中' : a.activity_status === 'PAUSED' ? '已暂停' : '已结束'} size="small"
                      color={a.activity_status === 'RUNNING' ? 'success' : 'default'} />
                  </TableCell>
                  <TableCell>{a.started_at ? new Date(a.started_at).toLocaleString('zh-CN') : '-'}</TableCell>
                  <TableCell>{fmtDuration(a.today_duration_seconds)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {/* Tab 3: Stats */}
      {tab === 3 && stats && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>团队统计报表</Typography>
          <Box sx={{ display: 'flex', gap: 3, mb: 3 }}>
            <Card sx={{ flex: 1, p: 2 }}><Typography color="text.secondary">总活动数</Typography><Typography variant="h4">{stats.total_activities}</Typography></Card>
            <Card sx={{ flex: 1, p: 2 }}><Typography color="text.secondary">总时长</Typography><Typography variant="h4">{fmtDuration(stats.total_duration_seconds)}</Typography></Card>
            <Card sx={{ flex: 1, p: 2 }}><Typography color="text.secondary">成员数</Typography><Typography variant="h4">{stats.member_count}</Typography></Card>
          </Box>
          <Typography variant="subtitle1" sx={{ mb: 1 }}>成员明细</Typography>
          <Table>
            <TableHead><TableRow><TableCell>成员</TableCell><TableCell>活动数</TableCell><TableCell>总时长</TableCell></TableRow></TableHead>
            <TableBody>
              {stats.per_member.map((m) => (
                <TableRow key={m.user_id}>
                  <TableCell>{m.username}</TableCell>
                  <TableCell>{m.activity_count}</TableCell>
                  <TableCell>{fmtDuration(m.total_duration_seconds)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      {/* Edit Dialog */}
      <EditTeamDialog open={editOpen} onClose={() => setEditOpen(false)} teamId={teamId} name={editName} desc={editDesc} />
    </Box>
  );
}

// ── Member Management Sub-Component ───────────────────────

function MemberManagement({ teamId, members, onRefresh }: { teamId: string; members: any[]; onRefresh: () => void }) {
  const [addOpen, setAddOpen] = useState(false);
  const [addUserId, setAddUserId] = useState('');
  const [addRole, setAddRole] = useState('member');
  const [submitting, setSubmitting] = useState(false);
  const { addMember, removeMember } = useTeamStore();

  const handleAdd = async () => {
    if (!addUserId.trim()) return;
    setSubmitting(true);
    try {
      await addMember(teamId, addUserId.trim(), addRole);
      setAddOpen(false); setAddUserId(''); onRefresh();
    } catch { /* error shown via store */ } finally { setSubmitting(false); }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<Add />} onClick={() => setAddOpen(true)}>
          添加成员
        </Button>
      </Box>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>用户名</TableCell>
            <TableCell>邮箱</TableCell>
            <TableCell>角色</TableCell>
            <TableCell>加入时间</TableCell>
            <TableCell>操作</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {members.map((m) => (
            <TableRow key={m.user_id}>
              <TableCell>{m.username}</TableCell>
              <TableCell>{m.email}</TableCell>
              <TableCell>
                <Chip label={m.role === 'admin' ? '管理员' : '成员'} size="small"
                  color={m.role === 'admin' ? 'primary' : 'default'} />
              </TableCell>
              <TableCell>{new Date(m.joined_at).toLocaleDateString('zh-CN')}</TableCell>
              <TableCell>
                <Tooltip title="移除">
                  <IconButton color="error" onClick={() => setDelMember(m.user_id)}>
                    <Delete />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Add Member Dialog */}
      <Dialog open={addOpen} onClose={() => setAddOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>添加成员</DialogTitle>
        <DialogContent sx={{ mt: 1 }}>
          <TextField fullWidth label="用户ID" value={addUserId} onChange={(e) => setAddUserId(e.target.value)} sx={{ mb: 2 }} autoFocus />
          <FormControl fullWidth>
            <InputLabel>角色</InputLabel>
            <Select value={addRole} label="角色" onChange={(e) => setAddRole(e.target.value)}>
              <MenuItem value="member">成员</MenuItem>
              <MenuItem value="admin">管理员</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleAdd} disabled={!addUserId.trim() || submitting}>
            {submitting ? '添加中...' : '添加'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirm */}
      <ConfirmDialog open={!!delMember} title="移除成员" content="确定要移除该成员吗？"
        onConfirm={async () => { if (delMember) { await removeMember(teamId, delMember); setDelMember(null); onRefresh(); } }}
        onCancel={() => setDelMember(null)} />
    </Box>
  );
}

// ── Edit Team Dialog ──────────────────────────────────────

function EditTeamDialog({ open, onClose, teamId, name, desc }: {
  open: boolean; onClose: () => void; teamId: string; name: string; desc: string;
}) {
  const [n, setN] = useState(name);
  const [d, setD] = useState(desc);
  const [submitting, setSubmitting] = useState(false);
  const updateTeam = useTeamStore((s) => s.updateTeam);

  const handleSubmit = async () => {
    if (!n.trim()) return;
    setSubmitting(true);
    try {
      await updateTeam(teamId, { name: n.trim(), description: d.trim() });
      onClose();
    } catch { /* ignore */ } finally { setSubmitting(false); }
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>编辑团队</DialogTitle>
      <DialogContent sx={{ mt: 1 }}>
        <TextField fullWidth label="团队名称" value={n} onChange={(e) => setN(e.target.value)} sx={{ mb: 2 }} autoFocus />
        <TextField fullWidth label="团队描述" value={d} onChange={(e) => setD(e.target.value)} multiline rows={3} />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button variant="contained" onClick={handleSubmit} disabled={!n.trim() || submitting}>
          {submitting ? '保存中...' : '保存'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
