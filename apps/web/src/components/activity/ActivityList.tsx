/** Activity list component grouping by status. */

import React, { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Tabs,
  Tab,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import { useActivity } from '../../hooks/useActivity';
import ActivityCard from './ActivityCard';
import ActivityForm from './ActivityForm';
import type { Activity } from '@time-tracker/shared';

const ActivityList: React.FC = () => {
  const {
    runningActivities,
    pausedActivities,
    endedActivities,
    filteredActivities,
  } = useActivity();
  const [showForm, setShowForm] = useState(false);
  const [editingActivity, setEditingActivity] = useState<Activity | null>(null);
  const [activeTab, setActiveTab] = useState(0);

  const tabs = [
    { label: '全部', activities: filteredActivities },
    { label: `运行中 (${runningActivities.length})`, activities: runningActivities },
    { label: `已暂停 (${pausedActivities.length})`, activities: pausedActivities },
    { label: `已结束 (${endedActivities.length})`, activities: endedActivities },
  ];

  const currentActivities = tabs[activeTab].activities;

  const handleEdit = (activity: Activity) => {
    setEditingActivity(activity);
    setShowForm(true);
  };

  const handleClose = () => {
    setShowForm(false);
    setEditingActivity(null);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">活动</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditingActivity(null);
            setShowForm(true);
          }}
        >
          新建活动
        </Button>
      </Box>

      <Tabs
        value={activeTab}
        onChange={(_, v) => setActiveTab(v)}
        sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}
      >
        {tabs.map((tab, index) => (
          <Tab key={index} label={tab.label} />
        ))}
      </Tabs>

      {currentActivities.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography color="text.secondary">
            暂无活动，创建一个开始吧！
          </Typography>
        </Box>
      ) : (
        <Box>
          {currentActivities.map((activity) => (
            <ActivityCard
              key={activity.id}
              activity={activity}
              onEdit={handleEdit}
            />
          ))}
        </Box>
      )}

      <ActivityForm
        open={showForm}
        onClose={handleClose}
        activity={editingActivity}
      />
    </Box>
  );
};

export default ActivityList;
