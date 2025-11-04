/**
 * 버전관리 페이지
 * - ex-GPT 버전 관리
 */
import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
} from '@mui/material';

export default function VersionManagementPage() {
  const [version, setVersion] = useState('1.5');

  const handleUpdateVersion = () => {
    console.log('버전 수정:', version);
    // TODO: API 호출
    alert(`버전이 ${version}으로 수정되었습니다.`);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* 설명 */}
      <Typography variant="body1" sx={{ mb: 3, color: '#666' }}>
        * ex-GPT 버전 관리를 할 수 있습니다.
      </Typography>

      {/* 버전 관리 박스 */}
      <Paper elevation={3} sx={{ p: 4, maxWidth: 600 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 3, mb: 3 }}>
          <Typography variant="h6" sx={{ minWidth: 100 }}>
            버전관리
          </Typography>
          <TextField
            fullWidth
            value={version}
            onChange={(e) => setVersion(e.target.value)}
            size="medium"
          />
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            onClick={handleUpdateVersion}
            sx={{ minWidth: 120 }}
          >
            버전수정
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
