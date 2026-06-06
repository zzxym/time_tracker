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
    { label: 'All', activities: filteredActivities },
    { label: `Running (${runningActivities.length})`, activities: runningActivities },
    { label: `Paused (${pausedActivities.length})`, activities: pausedActivities },
    { label: `Ended (${endedActivities.length})`, activities: endedActivities },
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
        <Typography variant="h5">Activities</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            setEditingActivity(null);
            setShowForm(true);
          }}
        >
          New Activity
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
            No activities found. Create one to get started!
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
