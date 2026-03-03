/**
 * @decision DEC-ROUTE-001
 * @title Hash-based routing with Alpine.js
 * @status accepted
 * @rationale Replace AngularJS ngRoute with a lightweight hash router implemented
 * in plain JS + Alpine.js. Preserves bookmarkable URLs (#/single/8.8.8.8,
 * #/multiple). API paths use /api/ (not /ninfo/api/) per DEC-ROUTE-001.
 * No build step required — Alpine.js loaded from CDN.
 */

/* ---------------------------------------------------------------------------
 * Router — minimal hash-based router that drives x-show visibility
 * ---------------------------------------------------------------------------
 * Exposes a global `router` object (used by Alpine components via $store or
 * direct reference). Route changes happen via window.location.hash and the
 * `hashchange` event propagates state updates.
 */
(function () {
    'use strict';

    // ---------------------------------------------------------------------------
    // Router
    // ---------------------------------------------------------------------------

    const router = {
        view: 'single',   // 'single' | 'multiple'
        arg: '',

        _parse: function () {
            // hash format: #/single[/arg*] | #/multiple
            const hash = window.location.hash.slice(1); // remove leading #
            const parts = hash.replace(/^\//, '').split('/');
            const view = parts[0] || 'single';
            if (view === 'multiple') {
                this.view = 'multiple';
                this.arg = '';
            } else {
                this.view = 'single';
                // arg may contain slashes (ip6), rejoin
                this.arg = parts.slice(1).join('/');
            }
        },

        navigate: function (view, arg) {
            if (view === 'multiple') {
                window.location.hash = '#/multiple';
            } else {
                const path = arg ? '/single/' + arg : '/single';
                window.location.hash = '#' + path;
            }
        },

        init: function () {
            this._parse();
            window.addEventListener('hashchange', () => {
                this._parse();
                // Notify Alpine that the router changed
                document.dispatchEvent(new CustomEvent('router:changed'));
            });

            // Default redirect from empty hash
            if (!window.location.hash || window.location.hash === '#') {
                window.location.hash = '#/single';
            }
        },
    };

    window.ninfoRouter = router;

    // ---------------------------------------------------------------------------
    // Alpine.js store & components — registered after Alpine is ready
    // ---------------------------------------------------------------------------

    document.addEventListener('alpine:init', function () {

        // ------------------------------------------------------------------
        // Store: router state (reactive wrapper around ninfoRouter)
        // ------------------------------------------------------------------
        Alpine.store('route', {
            view: 'single',
            arg: '',
            sync: function () {
                this.view = ninfoRouter.view;
                this.arg  = ninfoRouter.arg;
            },
        });

        // Sync store whenever hash changes
        document.addEventListener('router:changed', function () {
            Alpine.store('route').sync();
        });

        // ------------------------------------------------------------------
        // Component: single — navbar search form + single-arg results view
        // ------------------------------------------------------------------

        /**
         * @decision DEC-ROUTE-001
         * singleComponent drives both the navbar search form (always visible)
         * and the single-result view. It reacts to route changes via a watcher
         * on $store.route.arg.
         */
        Alpine.data('singleComponent', function () {
            return {
                // Search form
                searchArg: '',

                // Result state
                arg: '',
                plugins: [],
                status: {
                    started: false,
                    running: 0,
                    success: 0,
                    error: 0,
                    empty: 0,
                },

                get activatedPlugins() {
                    return this.plugins.filter(p => p.checked);
                },

                get total() {
                    return this.activatedPlugins.length;
                },

                get barSuccessWidth() {
                    if (!this.total) return '0%';
                    return (100 * this.status.success / this.total) + '%';
                },

                get barEmptyWidth() {
                    if (!this.total) return '0%';
                    return (100 * this.status.empty / this.total) + '%';
                },

                get barErrorWidth() {
                    if (!this.total) return '0%';
                    return (100 * this.status.error / this.total) + '%';
                },

                resetStatus: function () {
                    this.status = {
                        started: false,
                        running: 0,
                        success: 0,
                        error: 0,
                        empty: 0,
                    };
                },

                lookup: function () {
                    if (this.searchArg.trim()) {
                        ninfoRouter.navigate('single', this.searchArg.trim());
                    }
                },

                scrollTo: function (pluginName) {
                    const el = document.getElementById('result_' + pluginName);
                    if (el) {
                        el.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        // Nudge up a bit to clear the fixed navbar (≈55 px)
                        setTimeout(function () {
                            window.scrollBy({ top: -55, behavior: 'smooth' });
                        }, 300);
                    }
                },

                _loadPlugins: async function () {
                    try {
                        const resp = await fetch('/api/plugins/');
                        const data = await resp.json();
                        this.plugins = data.plugins.map(p => ({
                            ...p,
                            checked: true,
                            running: false,
                            hasResult: false,
                            resultHtml: '',
                        }));
                    } catch (e) {
                        console.error('Failed to load plugins', e);
                    }
                },

                _fetchResults: async function () {
                    if (!this.arg) return;
                    this.resetStatus();
                    await this._loadPlugins();
                    if (!this.plugins.length) return;

                    const arg = this.arg;

                    this.activatedPlugins.forEach(plugin => {
                        plugin.running = true;
                        plugin.hasResult = false;
                        plugin.resultHtml = '';
                        this.status.started = true;
                        this.status.running++;

                        fetch('/api/plugins/' + plugin.name + '/html/' + arg)
                            .then(r => r.text())
                            .then(html => {
                                if (html && html.trim()) {
                                    plugin.resultHtml = html;
                                    plugin.hasResult = true;
                                    this.status.success++;
                                } else {
                                    plugin.hasResult = false;
                                    this.status.empty++;
                                }
                                plugin.running = false;
                                this.status.running--;
                            })
                            .catch(() => {
                                plugin.hasResult = false;
                                plugin.running = false;
                                this.status.running--;
                                this.status.error++;
                            });
                    });
                },

                init: function () {
                    // Sync search box with initial route arg
                    this.arg = ninfoRouter.arg;
                    this.searchArg = this.arg;

                    // React to route changes
                    document.addEventListener('router:changed', () => {
                        const newArg = ninfoRouter.arg;
                        this.searchArg = newArg;
                        if (ninfoRouter.view === 'single' && newArg !== this.arg) {
                            this.arg = newArg;
                            this._fetchResults();
                        } else if (ninfoRouter.view === 'single' && !this.plugins.length && newArg) {
                            this.arg = newArg;
                            this._fetchResults();
                        }
                    });

                    // Load results for initial route if arg present
                    if (ninfoRouter.view === 'single' && this.arg) {
                        this._fetchResults();
                    }
                },
            };
        });

        // ------------------------------------------------------------------
        // Component: multipleComponent — bulk lookup view
        // ------------------------------------------------------------------

        /**
         * @decision DEC-ROUTE-001
         * multipleComponent handles the Multiple view. It is isolated from
         * singleComponent — each manages its own plugin list and status.
         * The Extract API (/api/extract) splits whitespace-separated input
         * into individual args; each arg × each active plugin fires a request.
         */
        Alpine.data('multipleComponent', function () {
            return {
                q: '',
                plugins: [],
                args: [],
                status: {
                    started: false,
                    running: 0,
                    success: 0,
                    error: 0,
                    empty: 0,
                },

                get activatedPlugins() {
                    return this.plugins.filter(p => p.checked);
                },

                get total() {
                    return this.args.length * this.activatedPlugins.length;
                },

                get barSuccessWidth() {
                    if (!this.total) return '0%';
                    return (100 * this.status.success / this.total) + '%';
                },

                get barEmptyWidth() {
                    if (!this.total) return '0%';
                    return (100 * this.status.empty / this.total) + '%';
                },

                get barErrorWidth() {
                    if (!this.total) return '0%';
                    return (100 * this.status.error / this.total) + '%';
                },

                resetStatus: function () {
                    this.status = {
                        started: false,
                        running: 0,
                        success: 0,
                        error: 0,
                        empty: 0,
                    };
                    this.args = [];
                },

                toggleAll: function () {
                    const anyChecked = this.plugins.some(p => p.checked);
                    this.plugins.forEach(p => { p.checked = !anyChecked; });
                },

                _loadPlugins: async function () {
                    if (this.plugins.length) return; // already loaded
                    try {
                        const resp = await fetch('/api/plugins/');
                        const data = await resp.json();
                        this.plugins = data.plugins.map(p => ({
                            ...p,
                            checked: true,
                        }));
                    } catch (e) {
                        console.error('Failed to load plugins', e);
                    }
                },

                lookup: async function () {
                    if (!this.q.trim()) return;
                    this.resetStatus();

                    // Extract args from the text box via server
                    try {
                        const url = '/api/extract?q=' + encodeURIComponent(this.q);
                        const resp = await fetch(url);
                        const data = await resp.json();
                        this.args = data.args.map(a => ({
                            value: a,
                            // Each plugin result stored per-arg
                            results: {},
                        }));
                    } catch (e) {
                        console.error('Failed to extract args', e);
                        return;
                    }

                    if (!this.args.length) return;

                    this.args.forEach(argObj => {
                        this.activatedPlugins.forEach(plugin => {
                            this.status.started = true;
                            this.status.running++;

                            fetch('/api/plugins/' + plugin.name + '/html/' + argObj.value)
                                .then(r => r.text())
                                .then(html => {
                                    if (html && html.trim()) {
                                        argObj.results[plugin.name] = {
                                            html: html,
                                            hasResult: true,
                                            title: plugin.title,
                                        };
                                        this.status.success++;
                                    } else {
                                        argObj.results[plugin.name] = { hasResult: false };
                                        this.status.empty++;
                                    }
                                    this.status.running--;
                                    // Force Alpine reactivity on nested object mutation
                                    this.args = [...this.args];
                                })
                                .catch(() => {
                                    argObj.results[plugin.name] = { hasResult: false };
                                    this.status.running--;
                                    this.status.error++;
                                    this.args = [...this.args];
                                });
                        });
                    });
                },

                init: async function () {
                    await this._loadPlugins();
                },
            };
        });

        // Sync the route store once on Alpine init (router already parsed hash
        // synchronously at IIFE execution time below)
        Alpine.store('route').sync();

    }); // alpine:init

    // Initialise the router immediately — this IIFE runs when the deferred
    // script executes (after DOM parse, before Alpine starts). Reading
    // window.location.hash is synchronous and safe here.
    ninfoRouter.init();

})();
