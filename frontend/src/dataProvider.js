/**
 * react-admin Data Provider for FastAPI backend
 * FastAPI 응답 형식을 react-admin 형식으로 변환
 * Version: 2025-10-20T21:20 - Fixed HTTPS mixed content issue
 */

// HTTPS 환경에서는 절대 HTTPS URL 사용
const API_BASE = window.location.protocol === 'https:'
    ? `${window.location.origin}/api/v1`
    : `/api/v1`;

console.log('[dataProvider] API_BASE 초기화:', API_BASE);

/**
 * HTTP 클라이언트 (fetchUtils 사용하지 않음 - Mixed Content 방지)
 */
const httpClient = async (url, options = {}) => {
    // Mixed Content 방지: HTTP를 HTTPS로 강제 변환
    if (window.location.protocol === 'https:' && url.startsWith('http://')) {
        const originalUrl = url;
        url = url.replace('http://', 'https://');
        console.warn('[dataProvider] HTTP → HTTPS 변환:', originalUrl, '→', url);
    }

    // 기본 헤더 설정
    const headers = options.headers || new Headers();
    if (!headers.get('Content-Type') && options.method !== 'GET') {
        headers.set('Content-Type', 'application/json');
    }
    headers.set('Accept', 'application/json');

    // Authorization 토큰 추가
    const token = localStorage.getItem('authToken');
    if (token) {
        headers.set('Authorization', `Bearer ${token}`);
    } else {
        // 임시: 테스트 환경에서 인증 우회
        headers.set('X-Test-Auth', 'admin');
    }

    console.log('[dataProvider] 최종 요청 URL:', url);
    console.log('[dataProvider] 요청 메서드:', options.method || 'GET');

    // fetch 직접 사용
    const response = await fetch(url, {
        ...options,
        headers,
        credentials: 'include', // 세션 쿠키 포함
    });

    const text = await response.text();
    const json = text ? JSON.parse(text) : {};

    if (!response.ok) {
        throw new Error(json.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    return { status: response.status, headers: response.headers, body: text, json };
};

/**
 * Custom Data Provider
 * FastAPI 응답을 react-admin 형식에 맞춤
 */
const dataProvider = {
    /**
     * 목록 조회
     * FastAPI: { items: [...], total: 100, page: 1, limit: 50, total_pages: 2 }
     * react-admin: { data: [...], total: 100 }
     */
    getList: async (resource, params) => {
        const { page, perPage } = params.pagination;
        const { field, order } = params.sort;
        const filter = params.filter;

        // conversations 리소스는 /admin/conversations/simple 사용
        if (resource === 'conversations') {
            // 날짜 필터 처리
            const query = new URLSearchParams({
                page: page,
                limit: perPage,
                sort_by: field,
                order: order.toLowerCase(),
            });

            if (filter.start) {
                query.append('start', filter.start);
            }
            if (filter.end) {
                query.append('end', filter.end);
            }

            const url = `${API_BASE}/admin/conversations/simple?${query}`;
            const { json } = await httpClient(url);

            return {
                data: json.items.map(item => ({ ...item, id: item.id })),
                total: json.total,
            };
        }

        // notices 리소스는 /admin/notices 사용
        if (resource === 'notices') {
            const query = new URLSearchParams({
                skip: (page - 1) * perPage,
                limit: perPage,
                sort_by: field,
                order: order.toLowerCase(),
            });

            // 필터 추가
            if (filter.priority) {
                query.append('priority', filter.priority);
            }
            if (filter.is_active) {
                query.append('is_active', filter.is_active);
            }
            if (filter.is_important) {
                query.append('is_important', filter.is_important);
            }

            const url = `${API_BASE}/admin/notices?${query}`;
            const { json } = await httpClient(url);

            return {
                data: json.items.map(item => ({ ...item, id: item.id })),
                total: json.total,
            };
        }

        // satisfaction 리소스는 /admin/satisfaction 사용 (필터 지원)
        if (resource === 'satisfaction') {
            const query = new URLSearchParams({
                skip: (page - 1) * perPage,
                limit: perPage,
                sort_by: field,
                order: order.toLowerCase(),
            });

            // 필터 추가
            if (filter.rating) {
                query.append('rating', filter.rating);
            }
            if (filter.category) {
                query.append('category', filter.category);
            }
            if (filter.user_id) {
                query.append('user_id', filter.user_id);
            }

            const url = `${API_BASE}/admin/satisfaction?${query}`;
            const { json } = await httpClient(url);

            return {
                data: json.items.map(item => ({ ...item, id: item.id })),
                total: json.total,
            };
        }

        // departments 리소스는 /admin/departments/ 사용 (trailing slash 필수)
        if (resource === 'departments') {
            const query = new URLSearchParams({
                skip: (page - 1) * perPage,
                limit: perPage,
            });

            // 검색 필터 추가
            if (filter.search) {
                query.append('search', filter.search);
            }

            const url = `${API_BASE}/admin/departments/?${query}`;
            const { json } = await httpClient(url);

            return {
                data: json.items.map(item => ({ ...item, id: item.id })),
                total: json.total,  // 전체 부서 수
            };
        }

        // users 리소스 (배열 반환, trailing slash 필수)
        if (resource === 'users') {
            const query = new URLSearchParams({
                skip: (page - 1) * perPage,
                limit: perPage,
            });

            if (filter.search) query.append('search', filter.search);
            if (filter.department_id) query.append('department_id', filter.department_id);
            if (filter.is_active !== undefined) query.append('is_active', filter.is_active);

            const url = `${API_BASE}/admin/users/?${query}`;
            const { json } = await httpClient(url);

            return {
                data: json.map(item => ({ ...item, id: item.id })),
                total: json.length,
            };
        }

        // document-permissions 리소스 (pagination 형식)
        if (resource === 'document-permissions') {
            const query = new URLSearchParams({
                skip: (page - 1) * perPage,
                limit: perPage,
            });

            if (filter.document_id) query.append('document_id', filter.document_id);
            if (filter.department_id) query.append('department_id', filter.department_id);
            if (filter.approval_line_id) query.append('approval_line_id', filter.approval_line_id);

            const url = `${API_BASE}/admin/document-permissions?${query}`;
            const { json } = await httpClient(url);

            return {
                data: json.items.map(item => ({ ...item, id: item.id })),
                total: json.total,
            };
        }

        // approval-lines 리소스 (pagination 형식)
        if (resource === 'approval-lines') {
            const query = new URLSearchParams({
                skip: (page - 1) * perPage,
                limit: perPage,
            });

            if (filter.search) query.append('search', filter.search);

            const url = `${API_BASE}/admin/approval-lines?${query}`;
            const { json } = await httpClient(url);

            return {
                data: json.items.map(item => ({ ...item, id: item.id })),
                total: json.total,
            };
        }

        // 기본 처리: 다른 리소스들
        const query = new URLSearchParams({
            skip: (page - 1) * perPage,
            limit: perPage,
        });

        const url = `${API_BASE}/admin/${resource}?${query}`;
        const { json } = await httpClient(url);

        return {
            data: json.items || [],
            total: json.total || 0,
        };
    },

    /**
     * 단일 레코드 조회
     * FastAPI: { id: 1, ... }
     * react-admin: { data: { id: 1, ... } }
     */
    getOne: async (resource, params) => {
        let url;
        if (resource === 'conversations') {
            url = `${API_BASE}/admin/conversations/simple/${params.id}`;
        } else if (resource === 'departments') {
            url = `${API_BASE}/admin/departments/${params.id}`;
        } else if (resource === 'users') {
            url = `${API_BASE}/admin/users/${params.id}`;
        } else if (resource === 'document-permissions') {
            url = `${API_BASE}/admin/document-permissions/${params.id}`;
        } else if (resource === 'approval-lines') {
            url = `${API_BASE}/admin/approval-lines/${params.id}`;
        } else {
            url = `${API_BASE}/admin/${resource}/${params.id}`;
        }

        const { json } = await httpClient(url);
        return { data: json };
    },

    /**
     * 여러 레코드 조회
     */
    getMany: async (resource, params) => {
        // 여러 ID의 레코드를 조회
        const promises = params.ids.map(id =>
            httpClient(`${API_BASE}/admin/${resource}/${id}`)
        );
        const results = await Promise.all(promises);
        return {
            data: results.map(result => result.json)
        };
    },

    /**
     * 참조된 레코드 목록 조회
     */
    getManyReference: async (resource, params) => {
        const { page, perPage } = params.pagination;
        const { field, order } = params.sort;

        const query = new URLSearchParams({
            skip: (page - 1) * perPage,
            limit: perPage,
            [params.target]: params.id,
        });

        const url = `${API_BASE}/admin/${resource}?${query}`;
        const { json } = await httpClient(url);

        return {
            data: json.items || [],
            total: json.total || 0,
        };
    },

    /**
     * 레코드 생성
     */
    create: async (resource, params) => {
        let url;
        if (resource === 'conversations') {
            url = `${API_BASE}/admin/conversations/simple`;
        } else if (resource === 'departments') {
            url = `${API_BASE}/admin/departments/`;
        } else if (resource === 'users') {
            url = `${API_BASE}/admin/users/`;
        } else if (resource === 'document-permissions') {
            url = `${API_BASE}/admin/document-permissions`;
        } else if (resource === 'approval-lines') {
            url = `${API_BASE}/admin/approval-lines`;
        } else {
            url = `${API_BASE}/admin/${resource}`;
        }

        const { json } = await httpClient(url, {
            method: 'POST',
            body: JSON.stringify(params.data),
        });

        return { data: { ...params.data, id: json.id } };
    },

    /**
     * 레코드 수정
     */
    update: async (resource, params) => {
        let url;
        if (resource === 'conversations') {
            url = `${API_BASE}/admin/conversations/simple/${params.id}`;
        } else if (resource === 'departments') {
            url = `${API_BASE}/admin/departments/${params.id}`;
        } else if (resource === 'users') {
            url = `${API_BASE}/admin/users/${params.id}`;
        } else if (resource === 'document-permissions') {
            url = `${API_BASE}/admin/document-permissions/${params.id}`;
        } else if (resource === 'approval-lines') {
            url = `${API_BASE}/admin/approval-lines/${params.id}`;
        } else {
            url = `${API_BASE}/admin/${resource}/${params.id}`;
        }

        const { json } = await httpClient(url, {
            method: 'PUT',
            body: JSON.stringify(params.data),
        });

        return { data: json };
    },

    /**
     * 여러 레코드 수정
     */
    updateMany: async (resource, params) => {
        const promises = params.ids.map(id =>
            dataProvider.update(resource, { id, data: params.data })
        );
        const results = await Promise.all(promises);
        return { data: results.map(result => result.data.id) };
    },

    /**
     * 레코드 삭제
     */
    delete: async (resource, params) => {
        let url;
        if (resource === 'conversations') {
            url = `${API_BASE}/admin/conversations/simple/${params.id}`;
        } else if (resource === 'departments') {
            url = `${API_BASE}/admin/departments/${params.id}`;
        } else if (resource === 'users') {
            url = `${API_BASE}/admin/users/${params.id}`;
        } else if (resource === 'document-permissions') {
            url = `${API_BASE}/admin/document-permissions/${params.id}`;
        } else if (resource === 'approval-lines') {
            url = `${API_BASE}/admin/approval-lines/${params.id}`;
        } else {
            url = `${API_BASE}/admin/${resource}/${params.id}`;
        }

        const { json } = await httpClient(url, {
            method: 'DELETE',
        });

        return { data: json };
    },

    /**
     * 여러 레코드 삭제
     */
    deleteMany: async (resource, params) => {
        const promises = params.ids.map(id =>
            dataProvider.delete(resource, { id })
        );
        const results = await Promise.all(promises);
        return { data: results.map(result => result.data.id) };
    },
};

export default dataProvider;
