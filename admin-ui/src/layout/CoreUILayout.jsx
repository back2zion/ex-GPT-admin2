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
                width: '100%',
                maxWidth: '100%',
                margin: '0 auto',
                '& .RaLayout-appFrame': {
                    marginTop: '56px',
                    width: '100%',
                    maxWidth: '100%',
                },
                '& .RaLayout-contentWithSidebar': {
                    display: 'flex !important',
                    flexDirection: 'row !important',
                    transition: 'margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    maxWidth: '100% !important',
                    width: '100% !important',
                    margin: '0 auto !important',
                },
                '& .RaLayout-content': {
                    backgroundColor: '#f8f9fa',
                    padding: '16px',
                    minHeight: 'calc(100vh - 56px)',
                    flex: '1',
                    overflow: 'auto',
                    maxWidth: '100%',
                    width: '100%',
                    margin: '0 auto',
                    '& > *': {
                        maxWidth: '100%',
                        width: '100%',
                    },
                    '& .MuiContainer-root, & .MuiContainer-maxWidthLg, & .MuiContainer-maxWidthMd, & .MuiContainer-maxWidthSm, & .MuiContainer-maxWidthXl': {
                        maxWidth: '100% !important',
                        width: '100%',
                        padding: '0 16px',
                        margin: '0 auto',
                    },
                    '& .MuiPaper-root': {
                        maxWidth: '100%',
                        width: '100%',
                    },
                    '& .MuiGrid-container': {
                        maxWidth: '100%',
                        width: '100%',
                        margin: '0 auto',
                    },
                    '& .MuiGrid-item': {
                        paddingTop: '8px',
                        paddingLeft: '8px',
                    },
                    '& .RaList-main, & .RaList-content': {
                        maxWidth: '100%',
                        width: '100%',
                    },
                    '& .RaShow-main, & .RaEdit-main, & .RaCreate-main': {
                        maxWidth: '100%',
                        width: '100%',
                    }
                },
            }}
        />
    );
};

export default CoreUILayout;
