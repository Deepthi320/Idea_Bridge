/**
 * Idea Bridge Client Application
 */

// Application State
let state = {
  ideas: [],
  selectedIdea: null,
  filters: {
    search: '',
    category: 'All',
    stage: 'All',
    sort: 'votes'
  },
  stats: null
};

// DOM Elements
const dom = {
  // Stats
  statTotalIdeas: document.getElementById('statTotalIdeas'),
  statActiveProjects: document.getElementById('statActiveProjects'),
  statCollaborators: document.getElementById('statCollaborators'),
  statCompleted: document.getElementById('statCompleted'),

  // Filters & Search
  searchInput: document.getElementById('searchInput'),
  categoryFilter: document.getElementById('categoryFilter'),
  stageFilter: document.getElementById('stageFilter'),
  sortBy: document.getElementById('sortBy'),
  btnResetFilters: document.getElementById('btnResetFilters'),
  resultsCount: document.getElementById('resultsCount'),

  // Feed
  ideasGrid: document.getElementById('ideasGrid'),
  emptyState: document.getElementById('emptyState'),
  btnEmptyNew: document.getElementById('btnEmptyNew'),

  // New Idea Modal
  btnNewIdea: document.getElementById('btnNewIdea'),
  newIdeaModal: document.getElementById('newIdeaModal'),
  btnCloseNewModal: document.getElementById('btnCloseNewModal'),
  btnCancelNewModal: document.getElementById('btnCancelNewModal'),
  newIdeaForm: document.getElementById('newIdeaForm'),

  // Detail Modal
  detailModal: document.getElementById('detailModal'),
  btnCloseDetailModal: document.getElementById('btnCloseDetailModal'),
  detailCategory: document.getElementById('detailCategory'),
  detailStage: document.getElementById('detailStage'),
  detailTitle: document.getElementById('detailTitle'),
  detailAuthor: document.getElementById('detailAuthor'),
  detailDate: document.getElementById('detailDate'),
  detailVotes: document.getElementById('detailVotes'),
  detailDescription: document.getElementById('detailDescription'),
  detailTagsList: document.getElementById('detailTagsList'),
  stagesStepper: document.getElementById('stagesStepper'),
  advanceStageSelect: document.getElementById('advanceStageSelect'),
  btnUpdateStage: document.getElementById('btnUpdateStage'),
  btnVoteDetail: document.getElementById('btnVoteDetail'),
  detailVoteCount: document.getElementById('detailVoteCount'),
  btnDeleteIdea: document.getElementById('btnDeleteIdea'),

  // Collaborators
  collaboratorsCount: document.getElementById('collaboratorsCount'),
  collaboratorsList: document.getElementById('collaboratorsList'),
  btnToggleJoin: document.getElementById('btnToggleJoin'),
  joinForm: document.getElementById('joinForm'),
  btnCancelJoin: document.getElementById('btnCancelJoin'),

  // Comments
  commentsCount: document.getElementById('commentsCount'),
  commentsList: document.getElementById('commentsList'),
  commentForm: document.getElementById('commentForm'),
  commentAuthor: document.getElementById('commentAuthor'),
  commentContent: document.getElementById('commentContent'),
};

// Stage slug helper for CSS
function getStageClass(stage) {
  if (!stage) return 'stage-discovery';
  return 'stage-' + stage.toLowerCase().replace(/\s+/g, '-');
}

// Format date helper
function formatDate(isoStr) {
  if (!isoStr) return '';
  const date = new Date(isoStr);
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

// API Calls
async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    if (res.ok) {
      state.stats = await res.json();
      renderStats();
    }
  } catch (err) {
    console.error('Error fetching stats:', err);
  }
}

async function fetchIdeas() {
  try {
    const params = new URLSearchParams();
    if (state.filters.category && state.filters.category !== 'All') {
      params.append('category', state.filters.category);
    }
    if (state.filters.stage && state.filters.stage !== 'All') {
      params.append('stage', state.filters.stage);
    }
    if (state.filters.search.trim()) {
      params.append('search', state.filters.search.trim());
    }
    if (state.filters.sort) {
      params.append('sort', state.filters.sort);
    }

    const res = await fetch(`/api/ideas?${params.toString()}`);
    if (res.ok) {
      state.ideas = await res.json();
      renderIdeas();
    }
  } catch (err) {
    console.error('Error fetching ideas:', err);
  }
}

async function fetchIdeaDetail(id) {
  try {
    const res = await fetch(`/api/ideas/${id}`);
    if (res.ok) {
      state.selectedIdea = await res.json();
      renderDetailModal();
    }
  } catch (err) {
    console.error('Error fetching idea detail:', err);
  }
}

async function handleCreateIdea(e) {
  e.preventDefault();
  const payload = {
    title: document.getElementById('formTitle').value.trim(),
    category: document.getElementById('formCategory').value,
    stage: document.getElementById('formStage').value,
    description: document.getElementById('formDescription').value.trim(),
    tags: document.getElementById('formTags').value.trim(),
    target_role: document.getElementById('formTargetRole').value.trim(),
    author_name: document.getElementById('formAuthorName').value.trim() || 'Anonymous',
    author_email: document.getElementById('formAuthorEmail').value.trim()
  };

  try {
    const res = await fetch('/api/ideas', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonPayload(payload)
    });

    if (res.ok) {
      const created = await res.json();
      dom.newIdeaForm.reset();
      closeNewIdeaModal();
      await fetchIdeas();
      await fetchStats();
      openDetailModal(created.id);
    } else {
      const err = await res.json();
      alert(`Error: ${err.error || 'Failed to create idea'}`);
    }
  } catch (err) {
    console.error('Create idea error:', err);
    alert('Failed to connect to the server');
  }
}

async function handleVote(id, delta = 1, e) {
  if (e) e.stopPropagation();
  try {
    const res = await fetch(`/api/ideas/${id}/vote`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delta })
    });
    if (res.ok) {
      const result = await res.json();
      // Update local state
      const target = state.ideas.find(i => i.id === id);
      if (target) {
        target.votes = result.votes;
        renderIdeas();
      }
      if (state.selectedIdea && state.selectedIdea.id === id) {
        state.selectedIdea.votes = result.votes;
        dom.detailVoteCount.textContent = result.votes;
        dom.detailVotes.textContent = `${result.votes} votes`;
      }
      fetchStats();
    }
  } catch (err) {
    console.error('Vote error:', err);
  }
}

async function handleUpdateStage() {
  if (!state.selectedIdea) return;
  const newStage = dom.advanceStageSelect.value;
  try {
    const res = await fetch(`/api/ideas/${state.selectedIdea.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage: newStage })
    });
    if (res.ok) {
      const updated = await res.json();
      state.selectedIdea = updated;
      renderDetailModal();
      fetchIdeas();
      fetchStats();
    }
  } catch (err) {
    console.error('Update stage error:', err);
  }
}

async function handleDeleteIdea() {
  if (!state.selectedIdea) return;
  if (!confirm(`Are you sure you want to delete "${state.selectedIdea.title}"?`)) {
    return;
  }

  try {
    const res = await fetch(`/api/ideas/${state.selectedIdea.id}`, {
      method: 'DELETE'
    });
    if (res.ok) {
      closeDetailModal();
      fetchIdeas();
      fetchStats();
    }
  } catch (err) {
    console.error('Delete idea error:', err);
  }
}

async function handleAddComment(e) {
  e.preventDefault();
  if (!state.selectedIdea) return;

  const author = dom.commentAuthor.value.trim() || 'Anonymous';
  const content = dom.commentContent.value.trim();
  if (!content) return;

  try {
    const res = await fetch(`/api/ideas/${state.selectedIdea.id}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ author_name: author, content })
    });
    if (res.ok) {
      const comment = await res.json();
      state.selectedIdea.comments.push(comment);
      dom.commentContent.value = '';
      renderComments();
      fetchIdeas();
    }
  } catch (err) {
    console.error('Add comment error:', err);
  }
}

async function handleJoinSubmit(e) {
  e.preventDefault();
  if (!state.selectedIdea) return;

  const name = document.getElementById('joinName').value.trim();
  const role = document.getElementById('joinRole').value.trim();
  const contact = document.getElementById('joinContact').value.trim();

  try {
    const res = await fetch(`/api/ideas/${state.selectedIdea.id}/collaborators`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, role, contact_info: contact })
    });
    if (res.ok) {
      const collab = await res.json();
      state.selectedIdea.collaborators.push(collab);
      dom.joinForm.reset();
      dom.joinForm.classList.add('hidden');
      renderCollaborators();
      fetchIdeas();
      fetchStats();
    }
  } catch (err) {
    console.error('Join error:', err);
  }
}

// Rendering Functions
function renderStats() {
  if (!state.stats) return;
  dom.statTotalIdeas.textContent = state.stats.total_ideas;
  dom.statActiveProjects.textContent = state.stats.active_projects;
  dom.statCollaborators.textContent = state.stats.total_collaborators;
  dom.statCompleted.textContent = state.stats.completed_projects;
}

function renderIdeas() {
  dom.resultsCount.textContent = `${state.ideas.length} ideas`;

  if (state.ideas.length === 0) {
    dom.ideasGrid.innerHTML = '';
    dom.emptyState.classList.remove('hidden');
    return;
  }

  dom.emptyState.classList.add('hidden');
  dom.ideasGrid.innerHTML = state.ideas.map(idea => {
    const stageClass = getStageClass(idea.stage);
    const tags = idea.tags ? idea.tags.split(',').map(t => t.trim()).filter(Boolean) : [];

    return `
      <div class="idea-card" onclick="openDetailModal(${idea.id})">
        <div>
          <div class="card-top">
            <div class="card-badges">
              <span class="badge badge-category">${escapeHtml(idea.category)}</span>
              <span class="badge ${stageClass}">${escapeHtml(idea.stage)}</span>
            </div>
            <button class="card-votes-pill" onclick="handleVote(${idea.id}, 1, event)" title="Upvote this idea">
              ▲ <span>${idea.votes}</span>
            </button>
          </div>
          <h4 class="card-title">${escapeHtml(idea.title)}</h4>
          <p class="card-description">${escapeHtml(idea.description)}</p>

          ${tags.length > 0 ? `
            <div class="card-tags">
              ${tags.slice(0, 3).map(tag => `<span class="tag-pill">#${escapeHtml(tag)}</span>`).join('')}
              ${tags.length > 3 ? `<span class="tag-pill">+${tags.length - 3}</span>` : ''}
            </div>
          ` : ''}
        </div>

        <div class="card-footer">
          <span class="card-author">By ${escapeHtml(idea.author_name || 'Anonymous')}</span>
          <div class="card-stats">
            <span>💬 ${idea.comment_count || 0}</span>
            <span>👥 ${idea.collaborator_count || 0}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function renderDetailModal() {
  const idea = state.selectedIdea;
  if (!idea) return;

  dom.detailTitle.textContent = idea.title;
  dom.detailAuthor.textContent = idea.author_name || 'Anonymous';
  dom.detailDate.textContent = `Posted on ${formatDate(idea.created_at)}`;
  dom.detailVotes.textContent = `${idea.votes} votes`;
  dom.detailVoteCount.textContent = idea.votes;
  dom.detailDescription.textContent = idea.description;

  dom.detailCategory.textContent = idea.category;
  dom.detailStage.textContent = idea.stage;
  dom.detailStage.className = `badge ${getStageClass(idea.stage)}`;

  dom.advanceStageSelect.value = idea.stage;

  // Stepper highlight
  const stages = ['Discovery', 'Discussion', 'Looking for Team', 'In Progress', 'Completed'];
  const currentIndex = stages.indexOf(idea.stage);
  const nodes = dom.stagesStepper.querySelectorAll('.step-node');
  nodes.forEach((node, idx) => {
    if (idx <= currentIndex) {
      node.classList.add('active');
    } else {
      node.classList.remove('active');
    }
  });

  // Tags
  if (idea.tags) {
    const tags = idea.tags.split(',').map(t => t.trim()).filter(Boolean);
    dom.detailTagsList.innerHTML = tags.map(t => `<span class="tag-pill">#${escapeHtml(t)}</span>`).join(' ');
    dom.detailTagsList.parentElement.classList.remove('hidden');
  } else {
    dom.detailTagsList.innerHTML = '';
  }

  renderCollaborators();
  renderComments();

  dom.detailModal.classList.remove('hidden');
}

function renderCollaborators() {
  const collabs = state.selectedIdea.collaborators || [];
  dom.collaboratorsCount.textContent = collabs.length;

  if (collabs.length === 0) {
    dom.collaboratorsList.innerHTML = '<p class="text-muted" style="font-size: 0.85rem; color: #64748b;">No collaborators yet. Be the first to join this bridge!</p>';
    return;
  }

  dom.collaboratorsList.innerHTML = collabs.map(c => `
    <div class="collaborator-item">
      <div class="collab-info">
        <span class="collab-name">${escapeHtml(c.name)}</span>
        <span class="collab-role">${escapeHtml(c.role)}</span>
      </div>
      ${c.contact_info ? `<span class="collab-contact">${escapeHtml(c.contact_info)}</span>` : ''}
    </div>
  `).join('');
}

function renderComments() {
  const comments = state.selectedIdea.comments || [];
  dom.commentsCount.textContent = comments.length;

  if (comments.length === 0) {
    dom.commentsList.innerHTML = '<p class="text-muted" style="font-size: 0.85rem; color: #64748b;">No comments yet. Share your thoughts or feedback above!</p>';
    return;
  }

  dom.commentsList.innerHTML = comments.map(c => `
    <div class="comment-item">
      <div class="comment-header">
        <span class="comment-author">${escapeHtml(c.author_name || 'Anonymous')}</span>
        <span class="comment-time">${formatDate(c.created_at)}</span>
      </div>
      <div class="comment-content">${escapeHtml(c.content)}</div>
    </div>
  `).join('');
}

// Modal open/close helpers
function openNewIdeaModal() {
  dom.newIdeaModal.classList.remove('hidden');
  document.getElementById('formTitle').focus();
}

function closeNewIdeaModal() {
  dom.newIdeaModal.classList.add('hidden');
}

function openDetailModal(id) {
  fetchIdeaDetail(id);
}

function closeDetailModal() {
  dom.detailModal.classList.add('hidden');
  state.selectedIdea = null;
  dom.joinForm.classList.add('hidden');
}

// Helper: JSON serializer
function jsonPayload(obj) {
  return JSON.stringify(obj);
}

// Helper: HTML escape
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Debounce helper
function debounce(fn, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), wait);
  };
}

// Event Listeners
function setupEventListeners() {
  // Filters
  dom.searchInput.addEventListener('input', debounce(() => {
    state.filters.search = dom.searchInput.value;
    fetchIdeas();
  }, 250));

  dom.categoryFilter.addEventListener('change', () => {
    state.filters.category = dom.categoryFilter.value;
    fetchIdeas();
  });

  dom.stageFilter.addEventListener('change', () => {
    state.filters.stage = dom.stageFilter.value;
    fetchIdeas();
  });

  dom.sortBy.addEventListener('change', () => {
    state.filters.sort = dom.sortBy.value;
    fetchIdeas();
  });

  dom.btnResetFilters.addEventListener('click', () => {
    dom.searchInput.value = '';
    dom.categoryFilter.value = 'All';
    dom.stageFilter.value = 'All';
    dom.sortBy.value = 'votes';
    state.filters = { search: '', category: 'All', stage: 'All', sort: 'votes' };
    fetchIdeas();
  });

  // Modal interactions
  dom.btnNewIdea.addEventListener('click', openNewIdeaModal);
  dom.btnEmptyNew.addEventListener('click', openNewIdeaModal);
  dom.btnCloseNewModal.addEventListener('click', closeNewIdeaModal);
  dom.btnCancelNewModal.addEventListener('click', closeNewIdeaModal);

  dom.btnCloseDetailModal.addEventListener('click', closeDetailModal);
  dom.btnVoteDetail.addEventListener('click', () => {
    if (state.selectedIdea) {
      handleVote(state.selectedIdea.id, 1);
    }
  });

  dom.btnUpdateStage.addEventListener('click', handleUpdateStage);
  dom.btnDeleteIdea.addEventListener('click', handleDeleteIdea);

  // Forms
  dom.newIdeaForm.addEventListener('submit', handleCreateIdea);
  dom.commentForm.addEventListener('submit', handleAddComment);

  // Join form toggle
  dom.btnToggleJoin.addEventListener('click', () => {
    dom.joinForm.classList.toggle('hidden');
  });
  dom.btnCancelJoin.addEventListener('click', () => {
    dom.joinForm.classList.add('hidden');
  });
  dom.joinForm.addEventListener('submit', handleJoinSubmit);

  // Close modals on backdrop click
  window.addEventListener('click', (e) => {
    if (e.target === dom.newIdeaModal) closeNewIdeaModal();
    if (e.target === dom.detailModal) closeDetailModal();
  });

  // Escape key closes modals
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeNewIdeaModal();
      closeDetailModal();
    }
  });
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  fetchStats();
  fetchIdeas();
});
