const query = new URLSearchParams(window.location.search);
    const today = new Date();
    const requestedDate = query.get('date');
    const pad2 = (value) => String(value).padStart(2, '0');
    const fallbackDate = `${today.getFullYear()}-${pad2(today.getMonth() + 1)}-${pad2(today.getDate())}`;

    const extractYMD = (value) => {
        if (!value) return null;
        const chinese = value.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
        if (chinese) {
            const [, y, m, d] = chinese;
            return { y, m: pad2(m), d: pad2(d) };
        }
        const iso = value.match(/(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
        if (iso) {
            const [, y, m, d] = iso;
            return { y, m: pad2(m), d: pad2(d) };
        }
        return null;
    };

    const formatHyphen = (parts) => `${parts.y}-${parts.m}-${parts.d}`;
    const formatChinese = (parts) => `${parts.y}年${parts.m}月${parts.d}日`;

    const collectCandidates = (...values) => {
        const buckets = [];
        values.forEach((value) => {
            if (!value) return;
            const parts = extractYMD(value);
            if (!parts) {
                buckets.push(value);
                return;
            }
            const hyphen = formatHyphen(parts);
            const isChineseInput = /年/.test(value);
            if (isChineseInput) {
                buckets.push(formatChinese(parts));
            }
            buckets.push(hyphen);
        });
        return buckets;
    };

    const SAMPLE_SUMMARY = {
        metadata: {
            date: '2025-11-12',
            total_batches: 5,
            total_news_count: 150,
            last_update: '2025-11-12T15:35:00+08:00',
        },
        batches: [
            {
                batch_id: '15时35分',
                timestamp: '2025-11-12T15:35:00+08:00',
                stats: [
                    {
                        word_group: '中国 美国 经济',
                        count: 28,
                        percentage: 18.6,
                        news_list: [
                            {
                                title: '美就业疲软提振降息预期，人民币情绪修复',
                                url: 'https://example.com/news/1',
                                platform: 'wallstreetcn-hot',
                                platform_name: '华尔街见闻',
                                rank: 1,
                                ranks: [1],
                                occurrence_count: 1,
                                time_display: '15时35分',
                                is_new: false,
                                mobile_url: 'https://m.example.com/news/1',
                            },
                            {
                                title: '美股高位震荡，市场押注 12 月降息',
                                url: 'https://example.com/news/2',
                                platform: 'jin10-hot',
                                platform_name: '金十数据',
                                rank: 4,
                                time_display: '15时28分',
                                is_new: true,
                            },
                        ],
                    },
                    {
                        word_group: '新能源 供应链',
                        count: 16,
                        percentage: 11.2,
                        news_list: [
                            {
                                title: '国内动力电池开工率回升，三元再获海外大单',
                                url: 'https://example.com/news/3',
                                platform_name: '36氪热榜',
                                rank: 2,
                                time_display: '15时12分',
                            },
                            {
                                title: '锂价止跌，四川资源型小厂重启',
                                url: 'https://example.com/news/4',
                                platform_name: '知乎热榜',
                                rank: 8,
                                time_display: '15时05分',
                            },
                        ],
                    },
                ],
            },
            {
                batch_id: '14时50分',
                timestamp: '2025-11-12T14:50:00+08:00',
                stats: [
                    {
                        word_group: 'AI 芯片',
                        count: 22,
                        percentage: 14.2,
                        news_list: [
                            {
                                title: '国产 GPU 交付国内云厂商，推理性能获验证',
                                url: 'https://example.com/news/5',
                                platform_name: '微博热搜',
                                rank: 3,
                                time_display: '14时46分',
                                is_new: true,
                            },
                            {
                                title: '台系封测厂 2025 产能满排，AI 订单排到 Q3',
                                url: 'https://example.com/news/6',
                                platform_name: '东吴证券读报',
                                rank: 6,
                                time_display: '14时40分',
                            },
                        ],
                    },
                    {
                        word_group: '出海 电商',
                        count: 12,
                        percentage: 8.5,
                        news_list: [
                            {
                                title: '东南亚 11.11 GMV 创新高，中国品牌占 63%',
                                url: 'https://example.com/news/7',
                                platform_name: '抖音热榜',
                                rank: 5,
                                time_display: '14时33分',
                            },
                        ],
                    },
                ],
            },
        ],
    };

    const DASHBOARD_API_BASE_URL = window.HOTSPOT_DASHBOARD_BASE_URL || 'http://localhost:8000/api/v1';

    const buildApiUrl = (endpoint, params = {}) => {
        const normalizedBase = DASHBOARD_API_BASE_URL.replace(/\/$/, '');
        const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        const url = new URL(`${normalizedBase}${normalizedEndpoint}`);
        Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                url.searchParams.set(key, value);
            }
        });
        return url.toString();
    };

    const fetchDashboardJSON = async (endpoint, params = {}) => {
        const url = buildApiUrl(endpoint, params);
        const response = await fetch(url, { headers: { Accept: 'application/json' } });
        if (!response.ok) {
            throw new Error(`请求 ${endpoint} 失败 (${response.status})`);
        }
        const payload = await response.json().catch(() => null);
        return payload?.data ?? payload;
    };

    const SAMPLE_INCREMENTAL = {
        metadata: {
            date: '2025-11-12',
            batch_id: '15时35分',
            timestamp: '2025-11-12T15:35:00+08:00',
            new_news_count: 12,
        },
        stats: [
            {
                word_group: '中国 美国',
                count: 5,
                percentage: 41.6,
                news_list: [
                    {
                        title: '人民币中间价小幅调升，跨境资金流入回暖',
                        url: 'https://example.com/news/8',
                        platform_name: '财联社热度',
                        rank: 7,
                        time_display: '15时27分',
                        is_new: true,
                    },
                ],
            },
            {
                word_group: '光伏 储能',
                count: 4,
                percentage: 33.3,
                news_list: [
                    {
                        title: '欧洲户储回暖，国内逆变器龙头获 2 亿欧大单',
                        url: 'https://example.com/news/9',
                        platform_name: '雪球热榜',
                        rank: 9,
                        time_display: '15时20分',
                    },
                ],
            },
            {
                word_group: '消费 复苏',
                count: 3,
                percentage: 25.1,
                news_list: [
                    {
                        title: '黑五预售启动，跨境独立站单量翻倍',
                        url: 'https://example.com/news/10',
                        platform_name: '小红书热搜',
                        rank: 11,
                        time_display: '15时12分',
                        is_new: true,
                    },
                ],
            },
        ],
    };

    const dataState = {
        summarySource: 'sample',
        incrementalSource: 'sample',
    };

    const readInlineJSON = (id) => {
        const node = document.getElementById(id);
        if (!node) return null;
        const payload = node.textContent?.trim();
        if (!payload) return null;
        try {
            return JSON.parse(payload);
        } catch (error) {
            console.warn(`解析 ${id} 失败`, error);
            return null;
        }
    };

    const candidateDates = Array.from(new Set([
        ...collectCandidates(requestedDate),
        ...collectCandidates(fallbackDate),
        ...collectCandidates(SAMPLE_SUMMARY.metadata?.date),
    ].filter(Boolean)));

    const heroEls = {
        date: document.getElementById('metaDate'),
        batches: document.getElementById('metaBatch'),
        news: document.getElementById('metaNews'),
        updated: document.getElementById('metaUpdated'),
    };

    const MAX_NEWS_PER_GROUP = (() => {
        const possible = Number(window.HOTSPOT_STAT_NEWS_LIMIT);
        return Number.isFinite(possible) && possible > 0 ? possible : Infinity;
    })();

    const NEWS_SCROLL_VISIBLE_COUNT = (() => {
        const value = Number(window.HOTSPOT_NEWS_VISIBLE_COUNT);
        return Number.isFinite(value) && value > 0 ? value : 5;
    })();

    const CHAT_DEFAULTS = {
        inject_context: window.HOTSPOT_CHAT_INJECT_CONTEXT !== false,
        news_limit: Number(window.HOTSPOT_CHAT_NEWS_LIMIT) || 50,
        platforms: Array.isArray(window.HOTSPOT_CHAT_PLATFORMS) ? window.HOTSPOT_CHAT_PLATFORMS : undefined,
    };

    const batchTimelineEl = document.getElementById('batchTimeline');
    const batchBadgeEl = document.getElementById('batchBadge');
    const incrementalBadgeEl = document.getElementById('incrementalBadge');
    const incrementalMetaEl = document.getElementById('incrementalMeta');
    const incrementalStatsEl = document.getElementById('incrementalStats');

    const formatNumber = (value) => value?.toLocaleString?.('zh-CN') ?? '0';

    const formatTime = (isoString) => {
        if (!isoString) return '—';
        const date = new Date(isoString);
        return date.toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const formatDate = (isoString) => {
        if (!isoString) return '—';
        const date = new Date(isoString);
        return date.toLocaleString('zh-CN', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    const createStatCard = (stat) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'stat-card';
        wrapper.innerHTML = `
            <div class="stat-word">${stat.word_group}</div>
            <div class="stat-count">
                <strong>${stat.count}</strong>
                <span>条新闻 · ${stat.percentage ?? 0}%</span>
            </div>
            <div class="progress">
                <span style="width:${stat.percentage ?? 0}%"></span>
            </div>
        `;

        const newsList = document.createElement('div');
        newsList.className = 'news-list';

        const allNews = Array.isArray(stat.news_list) ? stat.news_list : [];
        const visibleNews = MAX_NEWS_PER_GROUP === Infinity ? allNews : allNews.slice(0, MAX_NEWS_PER_GROUP);

        visibleNews.forEach((news) => {
            const link = document.createElement('a');
            link.className = 'news-item';
            link.href = news.url || news.mobile_url || '#';
            link.target = '_blank';
            link.rel = 'noopener noreferrer';

            link.innerHTML = `
                <div class="news-title">${news.title}</div>
                <div class="news-meta">
                    <span>${news.platform_name || news.platform}</span>
                    <span>排名 #${news.rank ?? '—'}</span>
                    <span>${news.time_display || formatTime(news.timestamp)}</span>
                    ${news.is_new ? '<span class="pill">New</span>' : ''}
                </div>
            `;

            newsList.appendChild(link);
        });

        if (visibleNews.length > NEWS_SCROLL_VISIBLE_COUNT) {
            newsList.classList.add('news-list-scrollable');
            newsList.style.setProperty('--news-visible-count', NEWS_SCROLL_VISIBLE_COUNT);
        }

        if (MAX_NEWS_PER_GROUP !== Infinity && allNews.length > visibleNews.length) {
            const footer = document.createElement('div');
            footer.className = 'news-meta';
            footer.textContent = `还有 ${allNews.length - visibleNews.length} 条新闻，调整 HOTSPOT_STAT_NEWS_LIMIT 查看更多`;
            newsList.appendChild(footer);
        }

        wrapper.appendChild(newsList);
        return wrapper;
    };

    const createBatchCard = (batch, index) => {
        const card = document.createElement('article');
        card.className = 'batch-card';

        card.innerHTML = `
            <div class="batch-summary">
                <div>
                    <div class="batch-time">${batch.batch_id || `批次 ${index + 1}`}</div>
                    <div class="batch-meta">更新时间 · ${formatDate(batch.timestamp)}</div>
                </div>
                <div class="pill">${batch.stats?.length ?? 0} 个关键词组</div>
            </div>
        `;

        const statsGrid = document.createElement('div');
        statsGrid.className = 'stats-grid';

        (batch.stats || []).forEach((stat) => {
            statsGrid.appendChild(createStatCard(stat));
        });

        card.appendChild(statsGrid);
        return card;
    };

    const renderSummary = (data, options = {}) => {
        const { badgeText } = options;
        heroEls.date.textContent = data.metadata?.date || '—';
        heroEls.batches.textContent = `${data.metadata?.total_batches ?? 0} 批`;
        heroEls.news.textContent = `${formatNumber(data.metadata?.total_news_count ?? 0)} 条`;
        heroEls.updated.textContent = formatDate(data.metadata?.last_update);

        batchBadgeEl.textContent = badgeText ?? `${data.batches?.length ?? 0} 批记录`;

        batchTimelineEl.innerHTML = '';
        if (!data.batches?.length) {
            batchTimelineEl.innerHTML = '<div class="empty-state">暂无批次数据</div>';
            return;
        }

        data.batches.forEach((batch, index) => {
            batchTimelineEl.appendChild(createBatchCard(batch, index));
        });
    };

    const renderIncremental = (data, options = {}) => {
        const { badgeText } = options;
        incrementalBadgeEl.textContent = badgeText ?? (data.metadata?.batch_id || '—');

        incrementalMetaEl.innerHTML = '';
        const metaEntries = [
            { label: '批次时间', value: formatDate(data.metadata?.timestamp) },
            { label: '新增新闻', value: `${data.metadata?.new_news_count ?? 0} 条` },
            { label: '覆盖词组', value: `${data.stats?.length ?? 0} 组` },
        ];

        metaEntries.forEach((item) => {
            const card = document.createElement('div');
            card.className = 'incremental-card';
            card.innerHTML = `
                <div class="meta-label">${item.label}</div>
                <strong>${item.value}</strong>
            `;
            incrementalMetaEl.appendChild(card);
        });

        incrementalStatsEl.innerHTML = '';
        if (!data.stats?.length) {
            incrementalStatsEl.innerHTML = '<div class="empty-state">暂无新增数据</div>';
            return;
        }

        data.stats.forEach((stat) => {
            incrementalStatsEl.appendChild(createStatCard(stat));
        });
    };

    renderSummary(SAMPLE_SUMMARY, { badgeText: '样例视图' });
    renderIncremental(SAMPLE_INCREMENTAL, { badgeText: '样例批次' });

    const fetchWithFallback = async ({ label, loader }) => {
        for (const date of candidateDates) {
            try {
                const json = await loader(date);
                if (json) {
                    return { json, date };
                }
            } catch (error) {
                console.warn(`加载 ${label}(${date}) 失败`, error);
            }
        }
        return null;
    };

    const init = async () => {
        const inlineSummary = readInlineJSON('inline-summary');
        if (inlineSummary) {
            renderSummary(inlineSummary);
            dataState.summarySource = 'inline';
        } else {
            const summaryResult = await fetchWithFallback({
                label: 'summary API',
                loader: (date) => fetchDashboardJSON('/dashboard/summary', { date }),
            });
            if (summaryResult) {
                renderSummary(summaryResult.json);
                dataState.summarySource = 'api';
            } else if (dataState.summarySource === 'sample') {
                batchBadgeEl.textContent = '样例视图 · 等待 API 数据';
            }
        }

        const inlineIncremental = readInlineJSON('inline-incremental');
        if (inlineIncremental) {
            renderIncremental(inlineIncremental);
            dataState.incrementalSource = 'inline';
        } else {
            const incrementalResult = await fetchWithFallback({
                label: 'incremental API',
                loader: (date) => fetchDashboardJSON('/dashboard/incremental', { date }),
            });
            if (incrementalResult) {
                renderIncremental(incrementalResult.json);
                dataState.incrementalSource = 'api';
            } else if (dataState.incrementalSource === 'sample') {
                incrementalBadgeEl.textContent = '样例批次 · 等待 API 数据';
            }
        }
    };

    const bootstrapChatConsole = () => {
        const baseUrl = window.HOTSPOT_CHAT_BASE_URL || 'http://localhost:8000/api/v1';
        const formEl = document.getElementById('chatForm');
        const inputEl = document.getElementById('chatInput');
        const messagesEl = document.getElementById('chatMessages');
        const placeholderEl = document.getElementById('chatPlaceholder');
        const statusEl = document.getElementById('chatStatusBadge');
        const statusTextEl = statusEl?.querySelector('.chat-status-text');
        const sendButton = document.getElementById('chatSendButton');
        const stopButton = document.getElementById('chatStopButton');
        const newSessionButton = document.getElementById('chatNewSession');
        const quickPromptButtons = document.querySelectorAll('[data-chat-prompt]');
        const modalPortal = document.getElementById('chatModalPortal');
        const launcherButton = document.getElementById('chatLauncher');
        const closeButton = document.getElementById('chatCloseButton');
        const backdropEl = document.getElementById('chatBackdrop');
        const launcherHintEl = launcherButton?.querySelector('.chat-launcher-copy span');

        if (!formEl || !inputEl || !messagesEl) return;

        const state = {
            sessionId: null,
            sessionPromise: null,
            isStreaming: false,
            abortController: null,
            contextInjected: false,
            serviceReady: false,
        };

        const checkChatServiceStatus = async () => {
            try {
                const response = await fetch(`${baseUrl}/system/status`);
                if (!response.ok) throw new Error('服务状态异常');
                const payload = await response.json().catch(() => null);
                const statusText = payload?.data?.status || payload?.message || '服务可用';
                state.serviceReady = true;
                if (!state.sessionId && !state.isStreaming) {
                    setStatus(`服务可用 · ${statusText}`, 'idle');
                }
                return true;
            } catch (error) {
                state.serviceReady = false;
                setStatus('等待服务启动…', 'error');
                throw error;
            }
        };

        const defaultLauncherHint = launcherHintEl?.textContent?.trim() || '热点问答';
        const launcherCopyMap = {
            idle: defaultLauncherHint,
            connecting: '连接中…',
            ready: '随时提问',
            streaming: 'AI 正在分析…',
            error: '等待服务…',
        };

        let lastFocusedElement = null;

        const isModalOpen = () => modalPortal?.dataset.open === 'true';

        const scrollMessages = () => {
            requestAnimationFrame(() => {
                messagesEl.scrollTop = messagesEl.scrollHeight;
            });
        };

        const hidePlaceholder = () => {
            if (placeholderEl) placeholderEl.classList.add('hidden');
        };

        const showPlaceholder = () => {
            if (placeholderEl) placeholderEl.classList.remove('hidden');
        };

        const syncSendAvailability = () => {
            if (!sendButton) return;
            const hasText = Boolean(inputEl.value.trim());
            sendButton.disabled = !hasText || state.isStreaming;
        };

        const setBusy = (busy) => {
            state.isStreaming = busy;
            inputEl.disabled = busy;
            if (stopButton) stopButton.disabled = !busy;
            syncSendAvailability();
            if (!busy && isModalOpen()) inputEl.focus();
        };

        const setStatus = (text, variant = 'idle') => {
            if (statusEl) {
                statusEl.dataset.variant = variant;
                if (statusTextEl) statusTextEl.textContent = text;
            }
            if (launcherButton) {
                launcherButton.dataset.variant = variant;
            }
            if (launcherHintEl) {
                launcherHintEl.textContent = launcherCopyMap[variant] || defaultLauncherHint;
            }
        };

        const createMessageBubble = (role, content = '') => {
            hidePlaceholder();
            const bubble = document.createElement('div');
            bubble.className = `chat-message ${role}`;
            bubble.textContent = content;
            messagesEl.appendChild(bubble);
            scrollMessages();
            return bubble;
        };

        const summonChatSession = async (options = {}) => {
            if (options.reset) {
                state.sessionId = null;
                state.sessionPromise = null;
            }
            if (state.sessionId) return state.sessionId;
            if (state.sessionPromise) return state.sessionPromise;

            state.sessionPromise = (async () => {
                if (!state.serviceReady) {
                    await checkChatServiceStatus();
                }
                setStatus('正在连接聊天服务…', 'connecting');
                try {
                    const response = await fetch(`${baseUrl}/chat/sessions`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            inject_context: CHAT_DEFAULTS.inject_context,
                            news_limit: CHAT_DEFAULTS.news_limit,
                            platforms: CHAT_DEFAULTS.platforms,
                        }),
                    });
                    if (!response.ok) throw new Error('创建会话失败');
                    const payload = await response.json().catch(() => null);
                    const sessionId = payload?.data?.session_id;
                    if (!sessionId) throw new Error('后台未返回 session_id');
                    state.sessionId = sessionId;
                    state.contextInjected = false;
                    setStatus('已连接', 'ready');
                    return sessionId;
                } catch (error) {
                    setStatus(error.message || '连接失败', 'error');
                    throw error;
                }
            })();

            try {
                return await state.sessionPromise;
            } finally {
                state.sessionPromise = null;
            }
        };

        const updateModalState = (open) => {
            if (!modalPortal) return;
            modalPortal.dataset.open = open ? 'true' : 'false';
            modalPortal.setAttribute('aria-hidden', open ? 'false' : 'true');
            if (open) {
                document.body.dataset.chatOpen = 'true';
            } else {
                delete document.body.dataset.chatOpen;
            }
            if (launcherButton) {
                launcherButton.setAttribute('aria-expanded', open ? 'true' : 'false');
            }
            if (!open && lastFocusedElement instanceof HTMLElement) {
                lastFocusedElement.focus();
                lastFocusedElement = null;
            }
        };

        const openChatModal = () => {
            if (isModalOpen()) return;
            lastFocusedElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;
            updateModalState(true);
            requestAnimationFrame(() => {
                if (!state.isStreaming) {
                    inputEl.focus();
                } else if (stopButton) {
                    stopButton.focus();
                }
            });
            summonChatSession().catch((error) => {
                console.warn('打开聊天时创建会话失败', error);
                setStatus('等待服务启动…', 'error');
            });
        };

        const closeChatModal = () => {
            if (!isModalOpen()) return;
            updateModalState(false);
        };

        const resetConversation = async ({ createSession = false } = {}) => {
            if (state.abortController) {
                state.abortController.abort();
            }
            state.sessionId = null;
            state.contextInjected = false;
            state.isStreaming = false;
            messagesEl.querySelectorAll('.chat-message').forEach((node) => node.remove());
            showPlaceholder();
            setStatus('等待连接…', 'idle');
            syncSendAvailability();
            if (createSession) {
                try {
                    await summonChatSession({ reset: true });
                } catch (error) {
                    console.warn('无法重置聊天会话', error);
                }
            }
        };

        const streamAssistantReply = async (message) => {
            const question = message.trim();
            if (!question || state.isStreaming) return;

            createMessageBubble('user', question);
            const assistantBubble = createMessageBubble('assistant', '');
            inputEl.value = '';
            syncSendAvailability();
            setBusy(true);
            setStatus('AI 正在分析最新热点…', 'streaming');

            let sessionId;
            try {
                sessionId = await summonChatSession();
            } catch (error) {
                console.error('聊天会话获取失败', error);
                assistantBubble.classList.add('error');
                assistantBubble.textContent = error.message || '无法连接聊天服务';
                setBusy(false);
                setStatus('请求失败', 'error');
                return;
            }

            const injectContext = !state.contextInjected;
            state.contextInjected = true;
            const controller = new AbortController();
            state.abortController = controller;

            try {
                const response = await fetch(`${baseUrl}/chat/sessions/${sessionId}/messages/stream`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Accept: 'text/event-stream',
                    },
                    body: JSON.stringify({ message: question, inject_context: injectContext }),
                    signal: controller.signal,
                });

                if (!response.ok) {
                    throw new Error(`请求失败 (${response.status})`);
                }

                if (!response.body || !response.body.getReader) {
                    const fallback = await response.json().catch(() => null);
                    const reply = fallback?.data?.reply || '暂无回复内容';
                    assistantBubble.textContent = reply;
                    scrollMessages();
                } else {
                    const reader = response.body.getReader();
                    const decoder = new TextDecoder('utf-8');
                    let transcript = '';
                    let buffer = '';

                    const processEvent = (rawEvent) => {
                        const lines = rawEvent.split('\n');
                        const dataLine = lines.find((line) => line.startsWith('data:'));
                        if (!dataLine) return;
                        const payload = dataLine.replace(/^data:\s*/, '');
                        if (!payload) return;
                        try {
                            const parsed = JSON.parse(payload);
                            if (parsed.type === 'content') {
                                transcript += parsed.content || '';
                                assistantBubble.textContent = transcript;
                                scrollMessages();
                            } else if (parsed.type === 'done') {
                                transcript = parsed.full_reply || transcript;
                            } else if (parsed.type === 'error') {
                                throw new Error(parsed.error || '聊天失败');
                            }
                        } catch (parseError) {
                            console.warn('解析流式事件失败', parseError, payload);
                        }
                    };

                    while (true) {
                        const { value, done } = await reader.read();
                        if (done) break;
                        buffer += decoder.decode(value, { stream: true });

                        const segments = buffer.split('\n\n');
                        buffer = segments.pop() ?? '';
                        segments.forEach(processEvent);
                    }

                    const remaining = `${buffer}${decoder.decode()}`.trim();
                    if (remaining) {
                        remaining.split('\n\n').forEach(processEvent);
                    }

                    assistantBubble.textContent = transcript || 'AI 暂无补充';
                }

                setStatus('已就绪', 'ready');
            } catch (error) {
                if (error.name === 'AbortError') {
                    assistantBubble.classList.add('error');
                    assistantBubble.textContent = assistantBubble.textContent || '生成已终止';
                    setStatus('已停止', 'idle');
                } else {
                    console.error('聊天请求异常', error);
                    assistantBubble.classList.add('error');
                    assistantBubble.textContent = error.message || '聊天失败';
                    setStatus('请求失败', 'error');
                }
            } finally {
                if (state.abortController === controller) {
                    state.abortController = null;
                }
                setBusy(false);
            }
        };

        formEl.addEventListener('submit', (event) => {
            event.preventDefault();
            streamAssistantReply(inputEl.value);
        });

        inputEl.addEventListener('input', syncSendAvailability);

        syncSendAvailability();

        quickPromptButtons.forEach((button) => {
            button.addEventListener('click', () => {
                const prompt = button.getAttribute('data-chat-prompt');
                inputEl.value = prompt || '';
                syncSendAvailability();
                inputEl.focus();
            });
        });

        if (stopButton) {
            stopButton.addEventListener('click', () => {
                if (state.abortController) {
                    state.abortController.abort();
                }
            });
        }

        if (newSessionButton) {
            newSessionButton.addEventListener('click', () => {
                resetConversation({ createSession: true });
            });
        }

        if (launcherButton) {
            launcherButton.addEventListener('click', () => {
                if (isModalOpen()) {
                    closeChatModal();
                } else {
                    openChatModal();
                }
            });
        }

        if (closeButton) {
            closeButton.addEventListener('click', () => closeChatModal());
        }

        if (backdropEl) {
            backdropEl.addEventListener('click', () => closeChatModal());
        }

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && isModalOpen()) {
                event.preventDefault();
                closeChatModal();
            }
        });

        summonChatSession().catch((error) => {
            console.warn('初始会话创建失败', error);
            setStatus('等待服务启动…', 'error');
        });
    };

    document.addEventListener('DOMContentLoaded', () => {
        init();
        bootstrapChatConsole();
    });
