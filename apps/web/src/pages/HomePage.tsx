/** Home page with activity list. */

import React, { useEffect } from 'react';
import { Box } from '@mui/material';
import ActivityList from '../components/activity/ActivityList';
import TagFilter from '../components/tags/TagFilter';
import { useActivityStore } from '../stores/activityStore';
import { useTagStore } from '../stores/tagStore';

const HomePage: React.FC = () => {
  const fetchActivities = useActivityStore((s) => s.fetchActivities);
  const fetchTags = useTagStore((s) => s.fetchTags);

  useEffect(() => {
    fetchActivities();
    fetchTags();
  }, [fetchActivities, fetchTags]);

  return (
    <Box>
      <TagFilter />
      <ActivityList />
    </Box>
  );
};

export default HomePage;
