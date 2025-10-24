/**
 * CoreUI 스타일 레이아웃
 * Header + Sidebar + Main Content
 */
import { Layout } from 'react-admin';
import CoreUIAppBar from './CoreUIAppBar';
import CoreUISidebar from './CoreUISidebar';

const CoreUILayout = (props) => {
    return (
        <Layout
            {...props}
            appBar={CoreUIAppBar}
            sidebar={CoreUISidebar}
            sx={{
                '& .RaLayout-appFrame': {
                    marginTop: '56px',
                },
                '& .RaLayout-contentWithSidebar': {
                    display: 'flex !important',
                    flexDirection: 'row !important',
                    transition: 'margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    maxWidth: 'none !important',
                    width: '100% !important',
                },
                '& .RaLayout-content': {
                    backgroundColor: '#f8f9fa',
                    padding: '8px',
                    minHeight: 'calc(100vh - 56px)',
                    flex: '1',
                    overflow: 'auto',
                    maxWidth: 'none !important',
                    width: '100% !important',
                    '& > *': {
                        maxWidth: 'none !important',
                        width: '100% !important',
                    },
                    '& .MuiContainer-root, & .MuiContainer-maxWidthXl, & .MuiContainer-maxWidthLg, & .MuiContainer-maxWidthMd, & .MuiContainer-maxWidthSm': {
                        maxWidth: 'none !important',
                        width: '100% !important',
                        padding: '0 8px',
                    },
                    '& .MuiPaper-root': {
                        maxWidth: 'none !important',
                        width: '100% !important',
                    },
                    '& .MuiGrid-container': {
                        maxWidth: 'none !important',
                        width: '100% !important',
                        margin: '0',
                    },
                    '& .MuiGrid-item': {
                        paddingTop: '8px',
                        paddingLeft: '8px',
                    },
                    '& .MuiTableContainer-root': {
                        maxWidth: 'none !important',
                        width: '100% !important',
                    },
                    '& .MuiBox-root': {
                        maxWidth: 'none !important',
                    },
                    '& .RaList-main, & .RaList-content': {
                        maxWidth: 'none !important',
                        width: '100% !important',
                    }
                },
            }}
        />
    );
};

export default CoreUILayout;
