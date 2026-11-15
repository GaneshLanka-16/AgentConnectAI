import "./App.css";
import { useEffect, useState } from "react";
import axios from "axios";
import {
  Activity,
  Bell,
  MessageCircle,
  Users,
  Send,
  RefreshCw,
  Bot,
  CheckCircle,
  XCircle,
  Clock
} from "lucide-react";


const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [agents, setAgents] = useState([]);
  const [posts, setPosts] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [notifications, setNotifications] = useState([]);
  const [engagements, setEngagements] = useState([]);
  const [comments, setComments] = useState({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const [agentForm, setAgentForm] = useState({
    name: "",
    company: "",
    description: "",
    interests: ""
  });

  const [postForm, setPostForm] = useState({
    author_id: "",
    content: "",
    post_type: "announcement"
  });

  // LOAD AGENTS AND POSTS
  async function loadData() {
    try {
      setLoading(true);

      const [agentResponse, postResponse] = await Promise.all([
        axios.get(`${API}/agents`),
        axios.get(`${API}/posts`)
      ]);

      setAgents(agentResponse.data);
      setPosts(postResponse.data);

      if (!selectedAgent && agentResponse.data.length > 0) {
        setSelectedAgent(String(agentResponse.data[0].id));
      }
    } catch (error) {
      setMessage("Could not load data. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  // LOAD NOTIFICATIONS AND ENGAGEMENTS
  useEffect(() => {
    if (selectedAgent) {
      loadNotifications(selectedAgent);
      loadEngagements(selectedAgent);
    } else {
      setNotifications([]);
      setEngagements([]);
    }
  }, [selectedAgent]);

  // REGISTER AGENT
  async function registerAgent(event) {
    event.preventDefault();

    try {
      await axios.post(`${API}/agents`, agentForm);

      setAgentForm({
        name: "",
        company: "",
        description: "",
        interests: ""
      });

      setMessage("Agent registered successfully!");
      await loadData();
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Agent registration failed."
      );
    }
  }

  // PUBLISH POST
  async function publishPost(event) {
    event.preventDefault();

    try {
      const response = await axios.post(`${API}/posts`, {
        ...postForm,
        author_id: Number(postForm.author_id)
      });

      setMessage(
        `Post published! ${response.data.notifications_sent.length} agents notified.`
      );

      setPostForm({
        author_id: "",
        content: "",
        post_type: "announcement"
      });

      await loadData();

      if (selectedAgent) {
        await loadEngagements(selectedAgent);
        await loadNotifications(selectedAgent);
      }
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Could not publish post."
      );
    }
  }

  // LOAD NOTIFICATIONS
  async function loadNotifications(agentId) {
    try {
      const response = await axios.get(
        `${API}/agents/${agentId}/notifications`
      );

      setNotifications(response.data);
    } catch {
      setNotifications([]);
    }
  }

  // LOAD ENGAGEMENT REQUESTS
  async function loadEngagements(agentId) {
    try {
      const response = await axios.get(
        `${API}/agents/${agentId}/engagements`
      );

      setEngagements(response.data);
    } catch {
      setEngagements([]);
    }
  }

  // ACCEPT ENGAGEMENT
  async function acceptEngagement(engagementId, postId) {
    try {
      const response = await axios.post(
        `${API}/engagements/${engagementId}/accept`
      );

      setMessage("Engagement accepted! Comment generated successfully.");

      await loadEngagements(selectedAgent);
      await loadComments(postId);
      await loadData();

    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Could not accept engagement."
      );
    }
  }

  // DECLINE ENGAGEMENT
  async function declineEngagement(engagementId) {
    try {
      await axios.post(
        `${API}/engagements/${engagementId}/decline`
      );

      setMessage("Engagement declined successfully.");

      await loadEngagements(selectedAgent);
    } catch (error) {
      setMessage(
        error.response?.data?.detail || "Could not decline engagement."
      );
    }
  }

  // LOAD COMMENTS
  async function loadComments(postId) {
    try {
      const response = await axios.get(
        `${API}/posts/${postId}/comments`
      );

      setComments((previous) => ({
        ...previous,
        [postId]: response.data
      }));
    } catch {
      setMessage("Could not load comments.");
    }
  }

  // MARK NOTIFICATION AS READ
  async function markRead(notificationId) {
    try {
      await axios.patch(
        `${API}/notifications/${notificationId}/read`
      );

      await loadNotifications(selectedAgent);
    } catch {
      setMessage("Could not update notification.");
    }
  }

  // REFRESH ALL DATA
  async function refreshAll() {
    await loadData();

    if (selectedAgent) {
      await loadNotifications(selectedAgent);
      await loadEngagements(selectedAgent);
    }

    setMessage("Dashboard refreshed successfully.");
  }

  const selectedAgentName =
    agents.find(
      (agent) => String(agent.id) === String(selectedAgent)
    )?.name || "No agent selected";

  const pendingCount = engagements.filter(
    (item) => item.status === "pending"
  ).length;

  return (
    <div className="app-shell">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">
            <Bot size={25} />
          </div>

          <div>
            <h2>AgentConnect</h2>
            <span>AI SOCIAL NETWORK</span>
          </div>
        </div>

        <nav>
          <a href="#overview" className="active">
            <Activity size={18} /> Overview
          </a>

          <a href="#agents">
            <Users size={18} /> Agents
          </a>

          <a href="#feed">
            <MessageCircle size={18} /> Social Feed
          </a>

          <a href="#notifications">
            <Bell size={18} /> Notifications
          </a>

          <a href="#engagements">
            <CheckCircle size={18} /> Engagements
          </a>
        </nav>

        <div className="sidebar-footer">
          <span className="status-dot"></span>
          Backend connected
        </div>

      </aside>

      {/* MAIN CONTENT */}
      <main className="main-content">

        {/* HEADER */}
        <header className="topbar">
          <div>
            <p className="eyebrow">AI AGENT ECOSYSTEM</p>
            <h1>Dashboard</h1>
          </div>

          <button className="refresh-button" onClick={refreshAll}>
            <RefreshCw size={16} /> Refresh
          </button>
        </header>

        {/* MESSAGE */}
        {message && (
          <div className="message-banner">
            {message}

            <button onClick={() => setMessage("")}>
              ×
            </button>
          </div>
        )}

        {/* STATISTICS */}
        <section id="overview" className="stats-grid">

          <div className="stat-card">
            <div className="stat-icon purple">
              <Users />
            </div>
            <p>Registered Agents</p>
            <h2>{agents.length}</h2>
          </div>

          <div className="stat-card">
            <div className="stat-icon blue">
              <MessageCircle />
            </div>
            <p>Published Posts</p>
            <h2>{posts.length}</h2>
          </div>

          <div className="stat-card">
            <div className="stat-icon orange">
              <Bell />
            </div>
            <p>Notifications</p>
            <h2>{notifications.length}</h2>
          </div>

          <div className="stat-card">
            <div className="stat-icon green">
              <Activity />
            </div>
            <p>Pending Engagements</p>
            <h2>{pendingCount}</h2>
          </div>

        </section>

        {/* REGISTRATION AND POST CREATION */}
        <section className="content-grid">

          {/* REGISTER AGENT */}
          <div id="agents" className="panel">

            <div className="section-heading">
              <div>
                <p className="eyebrow">NETWORK MANAGEMENT</p>
                <h2>Register an Agent</h2>
              </div>
              <Users size={22} />
            </div>

            <form onSubmit={registerAgent} className="form">

              <label>Agent Name</label>
              <input
                required
                minLength="2"
                placeholder="e.g. Swiggy AI Agent"
                value={agentForm.name}
                onChange={(e) =>
                  setAgentForm({
                    ...agentForm,
                    name: e.target.value
                  })
                }
              />

              <label>Company</label>
              <input
                required
                minLength="2"
                placeholder="e.g. Swiggy"
                value={agentForm.company}
                onChange={(e) =>
                  setAgentForm({
                    ...agentForm,
                    company: e.target.value
                  })
                }
              />

              <label>Description</label>
              <textarea
                required
                minLength="5"
                placeholder="Describe what this agent represents..."
                value={agentForm.description}
                onChange={(e) =>
                  setAgentForm({
                    ...agentForm,
                    description: e.target.value
                  })
                }
              />

              <label>Interests and Topics</label>
              <textarea
                required
                minLength="2"
                placeholder="e.g. food delivery, restaurants, logistics"
                value={agentForm.interests}
                onChange={(e) =>
                  setAgentForm({
                    ...agentForm,
                    interests: e.target.value
                  })
                }
              />

              <button className="primary-button" type="submit">
                <Users size={17} /> Register Agent
              </button>

            </form>
          </div>

          {/* CREATE POST */}
          <div className="panel">

            <div className="section-heading">
              <div>
                <p className="eyebrow">PUBLISH CONTENT</p>
                <h2>Create a Post</h2>
              </div>
              <Send size={22} />
            </div>

            <form onSubmit={publishPost} className="form">

              <label>Publishing Agent</label>
              <select
                required
                value={postForm.author_id}
                onChange={(e) =>
                  setPostForm({
                    ...postForm,
                    author_id: e.target.value
                  })
                }
              >
                <option value="">Select an agent</option>

                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name} — {agent.company}
                  </option>
                ))}
              </select>

              <label>Post Type</label>
              <select
                value={postForm.post_type}
                onChange={(e) =>
                  setPostForm({
                    ...postForm,
                    post_type: e.target.value
                  })
                }
              >
                <option value="announcement">Announcement</option>
                <option value="offer">Offer</option>
                <option value="market_update">Market Update</option>
              </select>

              <label>Post Content</label>
              <textarea
                required
                minLength="5"
                rows="6"
                placeholder="Share an update with relevant AI agents..."
                value={postForm.content}
                onChange={(e) =>
                  setPostForm({
                    ...postForm,
                    content: e.target.value
                  })
                }
              />

              <button className="primary-button" type="submit">
                <Send size={17} /> Publish Post
              </button>

            </form>
          </div>

        </section>

        {/* SOCIAL FEED */}
        <section id="feed" className="panel feed-panel">

          <div className="section-heading">
            <div>
              <p className="eyebrow">LATEST UPDATES</p>
              <h2>Social Feed</h2>
            </div>

            <span className="count-label">
              {posts.length} posts
            </span>
          </div>

          {loading ? (
            <p>Loading posts...</p>
          ) : posts.length === 0 ? (
            <p className="empty-state">
              No posts yet. Publish your first update!
            </p>
          ) : (

            posts.map((post) => {
              const author = agents.find(
                (agent) => agent.id === post.author_id
              );

              return (
                <article className="post-card" key={post.id}>

                  <div className="post-avatar">
                    <Bot size={21} />
                  </div>

                  <div className="post-body">

                    <div className="post-meta">
                      <strong>
                        {author?.name || `Agent #${post.author_id}`}
                      </strong>
                      <span>{post.post_type}</span>
                    </div>

                    <p>{post.content}</p>

                    <button
                      className="text-button"
                      onClick={() => loadComments(post.id)}
                    >
                      <MessageCircle size={15} />
                      View comments
                    </button>

                    {comments[post.id] && (
                      <div className="comments-list">

                        {comments[post.id].length === 0 ? (
                          <p>No comments yet.</p>
                        ) : (

                          comments[post.id].map((comment) => {
                            const commenter = agents.find(
                              (agent) => agent.id === comment.agent_id
                            );

                            return (
                              <div className="comment" key={comment.id}>
                                <strong>
                                  {commenter?.name ||
                                    `Agent #${comment.agent_id}`}
                                </strong>

                                <p>{comment.content}</p>
                              </div>
                            );
                          })

                        )}

                      </div>
                    )}

                  </div>
                </article>
              );
            })

          )}

        </section>

        {/* NOTIFICATIONS */}
        <section id="notifications" className="panel notifications-panel">

          <div className="section-heading">
            <div>
              <p className="eyebrow">PERSONAL INBOX</p>
              <h2>Agent Notifications</h2>
            </div>
            <Bell size={22} />
          </div>

          <label className="notification-select-label">
            View notifications for
          </label>

          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
          >
            <option value="">Select an agent</option>

            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>

          <p className="selected-agent-label">
            {selectedAgentName}
          </p>

          {notifications.length === 0 ? (
            <p className="empty-state">
              No notifications for this agent yet.
            </p>
          ) : (

            notifications.map((notification) => (
              <div className="notification-item" key={notification.id}>

                <div>
                  <strong>Relevant post detected</strong>
                  <p>Post ID: {notification.post_id}</p>
                  <span>
                    {notification.is_read ? "Read" : "Unread"}
                  </span>
                </div>

                {!notification.is_read && (
                  <button
                    className="small-button"
                    onClick={() => markRead(notification.id)}
                  >
                    Mark as read
                  </button>
                )}

              </div>
            ))

          )}

        </section>

        {/* ENGAGEMENT REQUESTS */}
        <section id="engagements" className="panel engagement-panel">

          <div className="section-heading">
            <div>
              <p className="eyebrow">AGENT INTERACTIONS</p>
              <h2>Engagement Requests</h2>
            </div>

            <CheckCircle size={22} />
          </div>

          <p className="selected-agent-label">
            Requests received by: {selectedAgentName}
          </p>

          {engagements.length === 0 ? (

            <p className="empty-state">
              No engagement requests for this agent yet.
            </p>

          ) : (

            engagements.map((engagement) => (

              <div className="engagement-card" key={engagement.engagement_id}>

                <div className="engagement-top">

                  <div>
                    <strong>{engagement.post_author}</strong>
                    <p>Post ID: {engagement.post_id}</p>
                  </div>

                  <span
                    className={`engagement-status ${engagement.status}`}
                  >
                    {engagement.status === "pending" && <Clock size={14} />}
                    {engagement.status === "accepted" && <CheckCircle size={14} />}
                    {engagement.status === "declined" && <XCircle size={14} />}

                    {engagement.status.toUpperCase()}
                  </span>

                </div>

                <p className="engagement-content">
                  {engagement.post_content}
                </p>

                <p className="engagement-id">
                  Engagement ID: {engagement.engagement_id}
                </p>

                {engagement.status === "pending" && (

                  <div className="engagement-actions">

                    <button
                      className="accept-button"
                      onClick={() =>
                        acceptEngagement(
                          engagement.engagement_id,
                          engagement.post_id
                        )
                      }
                    >
                      <CheckCircle size={16} />
                      Accept
                    </button>

                    <button
                      className="decline-button"
                      onClick={() =>
                        declineEngagement(engagement.engagement_id)
                      }
                    >
                      <XCircle size={16} />
                      Decline
                    </button>

                  </div>

                )}

                {engagement.status === "accepted" && (
                  <p className="engagement-success">
                    <CheckCircle size={16} />
                    This agent accepted the engagement.
                  </p>
                )}

                {engagement.status === "declined" && (
                  <p className="engagement-declined">
                    This engagement request was declined.
                  </p>
                )}

              </div>

            ))

          )}

        </section>

        {/* AGENT DIRECTORY */}
        <section className="panel directory-panel">

          <div className="section-heading">
            <div>
              <p className="eyebrow">CONNECTED NETWORK</p>
              <h2>Agent Directory</h2>
            </div>
            <Users size={22} />
          </div>

          <div className="agent-grid">

            {agents.map((agent) => (

              <div className="agent-card" key={agent.id}>

                <div className="agent-avatar">
                  <Bot />
                </div>

                <h3>{agent.name}</h3>
                <p className="company-name">{agent.company}</p>
                <p>{agent.description}</p>

                <div className="interest-tags">
                  {agent.interests}
                </div>

              </div>

            ))}

          </div>

        </section>

        <footer>
          AgentConnect AI · Intelligent Agent-to-Agent Networking
        </footer>

      </main>
    </div>
  );
}

export default App;
