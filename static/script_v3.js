/**
 * 🎰 LarlBot Dashboard v3.0 - PRODUCTION READY
 * 
 * CRITICAL FIXES:
 * ✅ Timezone-aware timestamps (EST display with proper formatting)
 * ✅ Previous Results tab fully functional
 * ✅ Proper API timestamp capture (not page refresh time)
 * ✅ Tab switching with data loading on demand
 * ✅ Comprehensive error handling
 * ✅ Production-grade code structure
 */

// ============================================================================
// CONFIG
// ============================================================================

const CONFIG = {
    API_ENDPOINTS: {
        stats: '/api/stats',
        ranked_bets: '/api/ranked-bets',
        previous_results: '/api/previous-results'
    },
    REFRESH_INTERVAL: 30000,  // 30 seconds
    API_TIMEOUT: 10000,       // 10 seconds
    TIMEZONE: 'America/Detroit'
};

// ============================================================================
// STATE - Single source of truth
// ============================================================================

const DASHBOARD_STATE = {
    stats: null,
    ranked_bets: null,
    previous_results: null,
    last_api_update: null,
    activeTab: 'today',
    
    setStats(stats) {
        if (!stats || !stats.timestamp) {
            console.error('❌ Invalid stats:', stats);
            throw new Error('Stats missing required timestamp');
        }
        this.stats = stats;
        this.last_api_update = stats.timestamp;
        console.log('✅ Stats updated:', {
            timestamp: this.last_api_update,
            winRate: stats.win_rate,
            record: stats.record
        });
    },
    
    setRankedBets(bets) {
        if (!bets) {
            console.error('❌ Invalid ranked bets:', bets);
            throw new Error('Ranked bets missing data');
        }
        this.ranked_bets = bets;
        console.log('✅ Ranked bets updated:', {
            total: bets.total_top10,
            active: bets.active_count,
            completed: bets.completed_count
        });
    },
    
    setPreviousResults(results) {
        if (!Array.isArray(results)) {
            console.error('❌ Invalid previous results:', results);
            throw new Error('Previous results must be an array');
        }
        this.previous_results = results;
        console.log(`✅ Previous results updated: ${results.length} bets`);
    },
    
    getLastApiUpdate() {
        return this.last_api_update;
    }
};

// ============================================================================
// API - Centralized API calls
// ============================================================================

const API = {
    async fetchStats() {
        console.log('📊 Fetching stats...');
        try {
            const response = await this.fetchWithTimeout(CONFIG.API_ENDPOINTS.stats);
            const stats = await response.json();
            
            if (!stats.timestamp) {
                throw new Error('Stats response missing timestamp');
            }
            
            console.log('✅ Stats received');
            return stats;
        } catch (error) {
            console.error('❌ Stats fetch failed:', error);
            throw error;
        }
    },
    
    async fetchRankedBets() {
        console.log('📥 Fetching ranked bets...');
        try {
            const response = await this.fetchWithTimeout(CONFIG.API_ENDPOINTS.ranked_bets);
            const data = await response.json();
            
            if (!Array.isArray(data.top_10)) {
                throw new Error('Ranked bets response missing top_10 array');
            }
            
            console.log('✅ Ranked bets received');
            return data;
        } catch (error) {
            console.error('❌ Ranked bets fetch failed:', error);
            throw error;
        }
    },
    
    async fetchPreviousResults() {
        console.log('📜 Fetching previous results...');
        try {
            const response = await this.fetchWithTimeout(CONFIG.API_ENDPOINTS.previous_results);
            const results = await response.json();
            
            if (!Array.isArray(results)) {
                throw new Error('Previous results must be an array');
            }
            
            console.log(`✅ Previous results received: ${results.length} bets`);
            return results;
        } catch (error) {
            console.error('❌ Previous results fetch failed:', error);
            throw error;
        }
    },
    
    async fetchWithTimeout(url) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), CONFIG.API_TIMEOUT);
        
        try {
            const response = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error(`Request timeout (${CONFIG.API_TIMEOUT}ms)`);
            }
            throw error;
        }
    }
};

// ============================================================================
// FORMAT - Formatting utilities
// ============================================================================

const FORMAT = {
    /**
     * Remove mascots from team names
     */
    cleanTeamName(teamName) {
        const mascots = [
            'Roadrunners', '49ers', 'Bearcats', 'Rebels', 'Crimson Tide', 'Tigers', 'Bulldogs',
            'Eagles', 'Bears', 'Wildcats', 'Cardinals', 'Trojans', 'Spartans', 'Buckeyes',
            'Wolverines', 'Cornhuskers', 'Sooners', 'Longhorns', 'Aggies', 'Razorbacks',
            'Volunteers', 'Gators', 'Seminoles', 'Hurricanes', 'Cavaliers', 'Tar Heels',
            'Blue Devils', 'Orange', 'Orangemen', 'Highlanders', 'Hornets', 'Jackrabbits',
            'Terrapins', 'Terps', 'Hoosiers', 'Hawkeyes', 'Nittany Lions', 'Golden Gophers',
            'Badgers', 'Fighting Illini', 'Boilermakers', 'Scarlet Knights', 'Huskies',
            'Red Raiders', 'Yellow Jackets', 'Demon Deacons', 'Wolfpack', 'Panthers',
            'Mountaineers', 'Jayhawks', 'Cyclones', 'Bison', 'Fighting Hawks'
        ];
        
        let cleaned = teamName;
        for (const mascot of mascots) {
            cleaned = cleaned.replace(new RegExp(`\\b${mascot}\\b`, 'gi'), '').trim();
        }
        return cleaned;
    },
    
    /**
     * Get winner display text based on bet type and result
     */
    getWinnerText(bet) {
        if (!bet.result) return '';
        
        // For SPREAD bets
        if (bet.bet_type === 'SPREAD') {
            const match = bet.recommendation.match(/([+-]?\d+\.?\d*)/);
            if (match) {
                const spread = match[1];
                const teamPart = bet.recommendation.split(/[+-]\d/)[0].trim();
                const cleanTeam = this.cleanTeamName(teamPart);
                // Only add + if spread doesn't already have a sign
                const sign = spread.startsWith('-') || spread.startsWith('+') ? '' : '+';
                return `${cleanTeam} ${sign}${spread}`;
            }
        }
        
        // For TOTAL bets
        if (bet.bet_type === 'TOTAL') {
            const match = bet.recommendation.match(/(UNDER|OVER)\s+(\d+\.?\d*)/i);
            if (match) {
                return `${match[1].toUpperCase()} ${match[2]}`;
            }
        }
        
        // For MONEYLINE bets
        if (bet.bet_type === 'MONEYLINE') {
            const cleanTeam = this.cleanTeamName(bet.recommendation);
            return cleanTeam;
        }
        
        // Fallback
        return bet.recommendation || bet.result;
    },
    
    /**
     * Format ISO timestamp to EST display format
     * Input: "2026-02-15T18:28:35.123456-05:00" (from server)
     * Output: "Feb 15, 2026, 6:28:35 PM"
     */
    formatTimestamp(isoString) {
        try {
            if (!isoString) {
                console.error('❌ No timestamp provided');
                return 'Unknown';
            }
            
            const date = new Date(isoString);
            
            // Validate date
            if (isNaN(date.getTime())) {
                console.error('❌ Invalid timestamp:', isoString);
                return 'Invalid';
            }
            
            // Format using EST timezone
            const options = {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                second: '2-digit',
                hour12: true,
                timeZone: CONFIG.TIMEZONE
            };
            
            const formatted = date.toLocaleString('en-US', options);
            console.log('✅ Timestamp formatted:', formatted);
            return formatted;
        } catch (error) {
            console.error('❌ Error formatting timestamp:', error);
            return 'Error';
        }
    }
};

// ============================================================================
// RENDER - All UI update functions
// ============================================================================

const RENDER = {
    /**
     * Update stats on BOTH tabs
     */
    updateStats(stats) {
        try {
            const updates = {
                'stat-winrate': `${stats.win_rate}%`,
                'stat-record': stats.record,
                'stat-total': stats.total_bets,
                'stat-winrate-previous': `${stats.win_rate}%`,
                'stat-record-previous': stats.record,
                'stat-total-previous': stats.total_bets
            };
            
            for (const [id, value] of Object.entries(updates)) {
                const el = document.getElementById(id);
                if (el) el.textContent = value;
            }
            
            console.log('✅ Stats rendered on both tabs');
        } catch (error) {
            console.error('❌ Error rendering stats:', error);
        }
    },
    
    /**
     * Update timestamp display - CRITICAL: Uses API time, not page refresh time
     */
    updateTimestamp(apiTimestamp) {
        try {
            if (!apiTimestamp) {
                console.error('❌ updateTimestamp called without timestamp');
                return;
            }
            
            const formatted = FORMAT.formatTimestamp(apiTimestamp);
            const el = document.getElementById('timestamp');
            if (el) {
                el.textContent = formatted;
                console.log('✅ Timestamp updated:', formatted);
            }
        } catch (error) {
            console.error('❌ Error updating timestamp:', error);
        }
    },
    
    /**
     * Render today's bets (active bets only)
     */
    renderTodaysBets(ranked) {
        try {
            const container = document.getElementById('top-10-container');
            if (!container) {
                console.error('❌ Container not found: top-10-container');
                return;
            }
            
            const activeBets = ranked.active_top10 || [];
            const completed = ranked.completed_count || 0;
            const total = ranked.total_top10 || 0;
            
            if (activeBets.length > 0) {
                // Show active bets in 2-column grid
                const html = activeBets
                    .map(item => this.createBetCard(item, 'today'))
                    .join('');
                container.innerHTML = html;
                console.log(`✅ Rendered ${activeBets.length} active bets`);
            } else if (completed > 0) {
                // All games finished
                container.innerHTML = `
                    <div class="games-finished-card">
                        <span class="games-finished-card-icon">✅</span>
                        <div class="games-finished-card-title">All Games Finished!</div>
                        <div class="games-finished-card-text">
                            All <strong>${total}</strong> games have completed.
                            <br/>Check the <strong>"Previous Results"</strong> tab to see today's outcomes.
                        </div>
                    </div>
                `;
                console.log('✅ Games finished card rendered');
            } else {
                container.innerHTML = '<div class="empty-state">No recommendations available.</div>';
            }
        } catch (error) {
            console.error('❌ Error rendering today\'s bets:', error);
            const container = document.getElementById('top-10-container');
            if (container) {
                container.innerHTML = `<div class="empty-state" style="color: #ff453a;">Error loading bets: ${error.message}</div>`;
            }
        }
    },
    
    /**
     * Render previous results grouped by date
     * Groups bets by date (Feb 16, Feb 15, etc.)
     * Color codes by WIN/LOSS result (GREEN/RED), not by confidence
     */
    renderPreviousResults(results) {
        try {
            const container = document.getElementById('results-container');
            if (!container) {
                console.error('❌ Container not found: results-container');
                return;
            }
            
            if (!results || results.length === 0) {
                container.innerHTML = '<div class="empty-state">No previous results yet.</div>';
                console.log('✅ Empty previous results rendered');
                return;
            }
            
            // Group by date
            const grouped = this.groupByDate(results);
            
            // Render each date group
            let html = '';
            let dateIndex = 0;
            const dates = Object.keys(grouped);
            const mostRecentDate = dates.length > 0 ? dates[0] : null; // First date is most recent (desc sorted)
            
            console.log(`📊 Rendering ${results.length} previous results across ${dates.length} dates`);
            
            for (const [date, bets] of Object.entries(grouped)) {
                // Count by RESULT (WIN/LOSS only, exclude PENDING)
                const wins = bets.filter(b => b.result === 'WIN').length;
                const losses = bets.filter(b => b.result === 'LOSS').length;
                const pending = bets.filter(b => b.result === 'PENDING').length;
                const total = wins + losses; // Exclude PENDING from total
                const winRate = total > 0 ? Math.round((wins / total) * 100) : 0;
                
                const isExpanded = (date === mostRecentDate); // Most recent date expanded by default
                const arrowIcon = isExpanded ? '▼' : '▶';
                const hiddenClass = isExpanded ? '' : 'hidden';
                
                // Color coding based on win rate (not confidence)
                let borderColor = 'rgba(139, 92, 246, 0.3)'; // Default purple
                let bgGradient = 'rgba(139, 92, 246, 0.1)';
                let iconColor = '#8b5cf6';
                
                if (total > 0) {
                    if (winRate >= 70) {
                        // High win rate - green
                        borderColor = 'rgba(34, 197, 94, 0.4)';
                        bgGradient = 'rgba(34, 197, 94, 0.1)';
                        iconColor = '#22c55e';
                    } else if (winRate >= 50) {
                        // Medium win rate - blue
                        borderColor = 'rgba(59, 130, 246, 0.4)';
                        bgGradient = 'rgba(59, 130, 246, 0.1)';
                        iconColor = '#3b82f6';
                    } else {
                        // Low win rate - red
                        borderColor = 'rgba(239, 68, 68, 0.4)';
                        bgGradient = 'rgba(239, 68, 68, 0.1)';
                        iconColor = '#ef4444';
                    }
                }
                
                // Format date for display (e.g., "Feb 16, 2026")
                const dateFormatted = this.formatDateForDisplay(date);
                
                // Show pending count if any
                const pendingBadge = pending > 0 ? `<span style="color: #f59e0b; margin-left: 0.5rem;">${pending} Pending</span>` : '';
                
                html += `
                    <div style="margin-bottom: 1.5rem;">
                        <div class="date-header-card" onclick="toggleDate('date-${dateIndex}')" 
                             style="cursor: pointer; user-select: none; padding: 1.2rem 1.5rem; 
                                    background: linear-gradient(135deg, ${bgGradient} 0%, rgba(0,0,0,0.02) 100%);
                                    border: 1.5px solid ${borderColor};
                                    border-radius: 12px;
                                    backdrop-filter: blur(20px);
                                    box-shadow: 0 4px 12px ${borderColor.replace('0.4', '0.15').replace('0.3', '0.15')};
                                    display: flex;
                                    align-items: center;
                                    justify-content: space-between;
                                    transition: all 0.3s ease;">
                            <div style="flex: 1; text-align: center;">
                                <div style="display: flex; align-items: center; justify-content: center; gap: 0.8rem;">
                                    <span style="font-size: 1.5rem;">${isExpanded ? '📅' : '📆'}</span>
                                    <div style="font-size: 1.2rem; font-weight: 700; color: white;">
                                        ${dateFormatted}
                                    </div>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; gap: 1rem;">
                                <div style="background: ${bgGradient}; border: 1px solid ${borderColor}; 
                                            padding: 0.4rem 0.8rem; border-radius: 8px; font-weight: 700; 
                                            font-size: 0.9rem; display: flex; align-items: center; gap: 0.5rem;">
                                    <span style="color: #22c55e;">${wins} Wins</span>
                                    <span style="color: rgba(255,255,255,0.5);">|</span>
                                    <span style="color: #ef4444;">${losses} Losses</span>
                                    ${pendingBadge}
                                </div>
                                <span id="arrow-date-${dateIndex}" style="font-size: 1.2rem; color: ${iconColor}; font-weight: bold;">
                                    ${arrowIcon}
                                </span>
                            </div>
                        </div>
                        <div id="date-${dateIndex}" class="bets-grid ${hiddenClass}" style="margin-top: 1.2rem;">
                            ${bets.map(bet => this.createBetCard(bet, 'previous')).join('')}
                        </div>
                    </div>
                `;
                dateIndex++;
            }
            
            container.innerHTML = html;
            console.log(`✅ Rendered ${results.length} previous results grouped by ${Object.keys(grouped).length} dates`);
        } catch (error) {
            console.error('❌ Error rendering previous results:', error);
            const container = document.getElementById('results-container');
            if (container) {
                container.innerHTML = `<div class="empty-state" style="color: #ff453a;">Error loading results: ${error.message}</div>`;
            }
        }
    },
    
    /**
     * Format date string for display (e.g., "2026-02-16" -> "Feb 16, 2026")
     */
    formatDateForDisplay(dateStr) {
        try {
            // Handle format: "2026-02-16" -> "Feb 16, 2026"
            const parts = dateStr.split('-');
            if (parts.length !== 3) return dateStr; // Return as-is if not expected format
            
            const year = parseInt(parts[0]);
            const month = parseInt(parts[1]) - 1; // JS months are 0-indexed
            const day = parseInt(parts[2]);
            
            const date = new Date(year, month, day);
            const options = {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            };
            
            return date.toLocaleString('en-US', options);
        } catch (error) {
            console.error('❌ Error formatting date:', error);
            return dateStr;
        }
    },
    
    /**
     * Group results by date
     */
    groupByDate(results) {
        const grouped = {};
        
        for (const bet of results) {
            const date = bet.date || 'Unknown Date';
            if (!grouped[date]) {
                grouped[date] = [];
            }
            grouped[date].push(bet);
        }
        
        // Sort dates descending (newest first)
        return Object.fromEntries(
            Object.entries(grouped).sort((a, b) => b[0].localeCompare(a[0]))
        );
    },
    
    /**
     * Create bet card HTML
     */
    createBetCard(item, mode) {
        try {
            // Handle both ranked_bets format and raw bet format
            const bet = item.full_bet || item;
            const rank = item.rank || '';
            const score = item.score || 0;
            
            // Determine card styling classes
            let cardClass = '';
            
            if (mode === 'previous') {
                // PREVIOUS RESULTS: Color by RESULT (WIN/LOSS/PENDING)
                // GREEN = WIN, RED = LOSS, YELLOW = PENDING
                if (bet.result === 'WIN') {
                    cardClass = 'win';
                } else if (bet.result === 'LOSS') {
                    cardClass = 'loss';
                } else if (bet.result === 'PENDING') {
                    cardClass = 'pending';
                }
                console.log(`📊 Previous result card: ${bet.game} -> ${bet.result} (${cardClass})`);
            } else {
                // TODAY'S BETS: All same color (GREEN) - consistent for active picks
                // All active/recommended bets use base card color (green)
                cardClass = ''; // No class = uses base .bet-card (green color)
                console.log(`📊 Today's bet card: ${bet.game} -> active pick (green)`);
            }
            
            const riskLabel = (bet.risk_tier || 'LOW RISK').match(/LOW|MODERATE|HIGH/)?.[0] || 'UNKNOWN';
            
            // Clean team names (remove mascots)
            const cleanGame = FORMAT.cleanTeamName(bet.game || 'N/A');
            
            // Result badge for top-right (square glass card design) - only for previous results
            let resultBadge = '';
            if (mode === 'previous' && bet.result) {
                let resultColor = '#8b5cf6'; // Default purple
                let resultBg = 'rgba(139, 92, 246, 0.15)';
                let resultBorder = 'rgba(139, 92, 246, 0.4)';
                
                if (bet.result === 'WIN') {
                    resultColor = '#22c55e';
                    resultBg = 'rgba(34, 197, 94, 0.15)';
                    resultBorder = 'rgba(34, 197, 94, 0.4)';
                } else if (bet.result === 'LOSS') {
                    resultColor = '#ef4444';
                    resultBg = 'rgba(239, 68, 68, 0.15)';
                    resultBorder = 'rgba(239, 68, 68, 0.4)';
                } else if (bet.result === 'PENDING') {
                    resultColor = '#f59e0b';
                    resultBg = 'rgba(245, 158, 11, 0.15)';
                    resultBorder = 'rgba(245, 158, 11, 0.4)';
                }
                
                resultBadge = `
                    <div style="background: ${resultBg}; 
                                border: 1.5px solid ${resultBorder}; 
                                padding: 0.5rem 0.8rem; 
                                border-radius: 8px; 
                                font-weight: 700; 
                                font-size: 0.75rem;
                                color: ${resultColor};
                                backdrop-filter: blur(10px);
                                box-shadow: 0 2px 8px ${resultBorder.replace('0.4', '0.2')};
                                text-align: center;
                                min-width: 50px;">
                        ${bet.result}
                    </div>
                `;
            }
            
            // Rank badge (for today's bets)
            const rankBadge = rank && mode !== 'previous' ? `<div class="bet-rank-badge">#${rank}</div>` : '';
            
            // Winner text (for previous results)
            const winnerText = mode === 'previous' && bet.result ? FORMAT.getWinnerText(bet) : '';
            
            // LarlScore - use item.score if available, or calculate from bet data
            let larlScore = score;
            if (!larlScore || larlScore === 0) {
                // Try to get from item's larl_score field
                larlScore = item.larl_score || bet.larl_score || 0;
                
                // If still no score, calculate it from confidence and edge
                if (!larlScore || larlScore === 0) {
                    const confidence = parseFloat(bet.confidence) || 0;
                    const edge = parseFloat(bet.edge) || 0;
                    if (confidence > 0 && edge > 0) {
                        // Simple score calculation: (confidence / 10) * edge
                        larlScore = (confidence / 10) * edge;
                    }
                }
            }
            
            // Get clean reasons - now properly formatted from backend
            const getCleanReasons = (reason) => {
                if (!reason) return [];
                
                // Split by newline (backend sends bullet-formatted already)
                let bullets = reason.split('\n')
                    .map(r => r.trim())
                    .filter(r => r && r.length > 5);
                
                // Remove bullet markers if present (we'll add them back in rendering)
                bullets = bullets.map(r => r.replace(/^[•\-]\s*/, '').trim());
                
                // Return max 4 bullets
                return bullets.slice(0, 4);
            };
            
            const filteredReasons = getCleanReasons(bet.reason);
            
            // "Why This Pick" section for today's bets (below stats)
            const whyThisPickSection = mode !== 'previous' && filteredReasons.length > 0 ? `
                <div class="bet-reason-box">
                    <div class="bet-reason-label">💡 Why This Pick</div>
                    <div class="bet-reason-text">
                        ${filteredReasons.map(r => `• ${r.trim()}`).join('<br/>')}
                    </div>
                </div>
            ` : '';
            
            return `
                <div class="bet-card ${cardClass}">
                    ${rankBadge}
                    <div class="bet-header" style="display: flex; align-items: start; justify-content: space-between; gap: 0.5rem;">
                        <div style="flex: 1; text-align: center;">
                            <div class="bet-game"><i class="fas fa-basketball"></i> ${cleanGame}</div>
                            <div class="bet-time"><i class="fas fa-clock"></i> ${bet.game_time || 'TBD'}</div>
                        </div>
                        ${resultBadge}
                    </div>
                    <div class="bet-box">
                        <div class="bet-type">${bet.bet_type || 'UNKNOWN'}</div>
                        <div class="bet-recommendation">${bet.recommendation || 'N/A'}</div>
                        <div class="bet-line"><i class="fas fa-chart-line"></i> FanDuel: ${bet.fanduel_line || 'N/A'}</div>
                    </div>
                    <div class="bet-stats">
                        <div class="bet-stat">
                            <div class="bet-stat-label">Confidence</div>
                            <div class="bet-stat-value">${bet.confidence || '?'}%</div>
                        </div>
                        <div class="bet-stat">
                            <div class="bet-stat-label">LarlScore</div>
                            <div class="bet-stat-value">${larlScore > 0 ? larlScore.toFixed(1) : 'N/A'}</div>
                        </div>
                        ${mode === 'previous' ? `
                            <div class="bet-stat">
                                <div class="bet-stat-label">Result</div>
                                <div class="bet-stat-value">${winnerText || bet.result || '—'}</div>
                            </div>
                        ` : `
                            <div class="bet-stat">
                                <div class="bet-stat-label">Prediction</div>
                                <div class="bet-stat-value" style="font-size: 0.7rem;">${bet.recommendation || 'N/A'}</div>
                            </div>
                        `}
                    </div>
                    ${whyThisPickSection}
                </div>
            `;
        } catch (error) {
            console.error('❌ Error creating bet card:', error);
            return `<div class="empty-state">Error displaying bet</div>`;
        }
    }
};

// ============================================================================
// TAB SWITCHING - Handle tab clicks and load appropriate data
// ============================================================================

window.showTab = function(tab) {
    console.log(`📑 Switching to tab: ${tab}`);
    
    const todayContent = document.getElementById('tab-content-today');
    const previousContent = document.getElementById('tab-content-previous');
    const todayBtn = document.getElementById('tab-today');
    const previousBtn = document.getElementById('tab-previous');
    
    // Hide all tabs
    if (todayContent) todayContent.style.display = 'none';
    if (previousContent) previousContent.style.display = 'none';
    
    // Reset all buttons
    if (todayBtn) {
        todayBtn.classList.remove('active');
        todayBtn.classList.add('inactive');
    }
    if (previousBtn) {
        previousBtn.classList.remove('active');
        previousBtn.classList.add('inactive');
    }
    
    if (tab === 'today') {
        if (todayContent) todayContent.style.display = 'block';
        if (todayBtn) {
            todayBtn.classList.remove('inactive');
            todayBtn.classList.add('active');
        }
        DASHBOARD_STATE.activeTab = 'today';
        console.log('✅ Today\'s Bets tab active');
    } else if (tab === 'previous') {
        if (previousContent) previousContent.style.display = 'block';
        if (previousBtn) {
            previousBtn.classList.remove('inactive');
            previousBtn.classList.add('active');
        }
        DASHBOARD_STATE.activeTab = 'previous';
        
        // Load previous results when tab is opened
        if (typeof window.loadPreviousResults === 'function') {
            console.log('📜 Calling loadPreviousResults...');
            window.loadPreviousResults();
        } else {
            console.error('❌ loadPreviousResults not yet defined');
        }
        console.log('✅ Previous Results tab active');
    }
};

// Mission Control removed - functionality moved to integrated dashboard tabs

// Toggle date collapse/expand
window.toggleDate = function(dateId) {
    const container = document.getElementById(dateId);
    const arrowId = `arrow-${dateId}`;
    const arrow = document.getElementById(arrowId);
    
    if (container) {
        const isVisible = !container.classList.contains('hidden');
        if (isVisible) {
            container.classList.add('hidden');
        } else {
            container.classList.remove('hidden');
        }
        if (arrow) {
            arrow.textContent = isVisible ? '▶' : '▼';
        }
        console.log(`📅 Toggled ${dateId}: ${isVisible ? 'collapsed' : 'expanded'}`);
    }
};

// Expose to window scope so HTML can call it
window.loadPreviousResults = async function() {
    console.log('📜 Loading previous results...');
    
    try {
        // Check if already loaded
        if (DASHBOARD_STATE.previous_results) {
            console.log('✅ Using cached previous results');
            RENDER.renderPreviousResults(DASHBOARD_STATE.previous_results);
            return;
        }
        
        // Fetch from API
        const results = await API.fetchPreviousResults();
        DASHBOARD_STATE.setPreviousResults(results);
        RENDER.renderPreviousResults(results);
    } catch (error) {
        console.error('❌ Error loading previous results:', error);
        const container = document.getElementById('results-container');
        if (container) {
            container.innerHTML = `
                <div class="empty-state" style="color: #ff453a;">
                    <i class="fas fa-exclamation-circle" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
                    <div style="margin-top: 0.5rem;">Error loading previous results: ${error.message}</div>
                </div>
            `;
        }
    }
};

// ============================================================================
// LOAD - Initial dashboard load
// ============================================================================

async function loadDashboard() {
    console.log('\n' + '='.repeat(70));
    console.log('🚀 DASHBOARD LOADING');
    console.log('='.repeat(70) + '\n');
    
    try {
        // Load in parallel: stats + ranked bets
        // (Previous results loads on-demand when tab is clicked)
        const [stats, ranked] = await Promise.all([
            API.fetchStats(),
            API.fetchRankedBets()
        ]);
        
        // Update state
        DASHBOARD_STATE.setStats(stats);
        DASHBOARD_STATE.setRankedBets(ranked);
        
        // Render UI
        RENDER.updateStats(stats);
        RENDER.renderTodaysBets(ranked);
        RENDER.updateTimestamp(DASHBOARD_STATE.getLastApiUpdate());
        
        console.log('✅ Dashboard loaded successfully\n');
    } catch (error) {
        console.error('❌ Dashboard loading failed:', error);
        const container = document.getElementById('top-10-container');
        if (container) {
            container.innerHTML = `
                <div class="empty-state" style="color: #ff453a;">
                    <i class="fas fa-exclamation-circle" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
                    <div style="margin-top: 0.5rem;">Failed to load dashboard: ${error.message}</div>
                    <div style="margin-top: 0.5rem; font-size: 0.9rem;">Retrying in 10 seconds...</div>
                </div>
            `;
        }
        
        // Retry after 10 seconds
        setTimeout(loadDashboard, 10000);
    }
}

// ============================================================================
// INIT - Initialization on page load
// ============================================================================

document.addEventListener('DOMContentLoaded', async function() {
    console.log('📱 Document ready - Initializing dashboard');
    
    // Load dashboard
    await loadDashboard();
    
    // Hide loading screen
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        setTimeout(() => {
            loadingScreen.classList.add('hidden');
            document.getElementById('app')?.classList.add('ready');
            console.log('✅ Dashboard ready - loading screen hidden');
        }, 500);
    }
    
    // Set up auto-refresh for stats + timestamp
    setInterval(async () => {
        console.log('🔄 Auto-refresh stats...');
        try {
            const stats = await API.fetchStats();
            DASHBOARD_STATE.setStats(stats);
            RENDER.updateStats(stats);
            RENDER.updateTimestamp(DASHBOARD_STATE.getLastApiUpdate());
        } catch (error) {
            console.warn('⚠️  Auto-refresh failed:', error);
        }
    }, CONFIG.REFRESH_INTERVAL);
});

console.log('✅ Dashboard script v3.0 loaded');
