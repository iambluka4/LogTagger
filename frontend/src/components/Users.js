import React, { useEffect, useState } from 'react';
import { getUsers, createUser, updateUser, deleteUser } from '../services/api';
import './Users.css';

function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Form states
  const [formMode, setFormMode] = useState('create'); // create or edit
  const [selectedUser, setSelectedUser] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    description: '',
    role: 'viewer'
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await getUsers();
      setUsers(res.data);
    } catch (error) {
      setError("Error fetching users: " + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      await createUser(formData);
      setSuccess("User created successfully");
      resetForm();
      fetchUsers();
    } catch (error) {
      setError("Error creating user: " + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    
    if (!selectedUser) return;
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const updateData = { ...formData };
      // Don't send password if it's empty (no change)
      if (!updateData.password) {
        delete updateData.password;
      }
      
      await updateUser(selectedUser.id, updateData);
      setSuccess("User updated successfully");
      resetForm();
      fetchUsers();
    } catch (error) {
      setError("Error updating user: " + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm("Are you sure you want to delete this user?")) return;
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      await deleteUser(userId);
      setSuccess("User deleted successfully");
      fetchUsers();
    } catch (error) {
      setError("Error deleting user: " + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  const selectUserForEdit = (user) => {
    setFormMode('edit');
    setSelectedUser(user);
    setFormData({
      username: user.username,
      password: '', // Leave password empty when editing
      description: user.description || '',
      role: user.role
    });
  };

  const resetForm = () => {
    setFormMode('create');
    setSelectedUser(null);
    setFormData({
      username: '',
      password: '',
      description: '',
      role: 'viewer'
    });
  };

  return (
    <div className="users-container">
      <h2>User Management</h2>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      
      <div className="users-layout">
        {/* User form */}
        <div className="user-form-container">
          <h3>{formMode === 'create' ? 'Create New User' : 'Edit User'}</h3>
          <form onSubmit={formMode === 'create' ? handleCreateUser : handleUpdateUser}>
            <div className="form-group">
              <label htmlFor="username">Username:</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                required
                disabled={formMode === 'edit'} // Username can't be changed when editing
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="password">
                {formMode === 'create' ? 'Password:' : 'New Password (leave empty to keep current):'}
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                required={formMode === 'create'} // Only required for new users
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="role">Role:</label>
              <select
                id="role"
                name="role"
                value={formData.role}
                onChange={handleInputChange}
                required
              >
                <option value="viewer">Viewer</option>
                <option value="analyst">Analyst</option>
                <option value="admin">Administrator</option>
              </select>
            </div>
            
            <div className="form-group">
              <label htmlFor="description">Description:</label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows="3"
              ></textarea>
            </div>
            
            <div className="form-actions">
              <button 
                type="submit" 
                className="primary-btn"
                disabled={loading}
              >
                {loading ? 'Saving...' : formMode === 'create' ? 'Create User' : 'Update User'}
              </button>
              
              {formMode === 'edit' && (
                <button 
                  type="button" 
                  className="secondary-btn"
                  onClick={resetForm}
                  disabled={loading}
                >
                  Cancel
                </button>
              )}
            </div>
          </form>
        </div>
        
        {/* Users list */}
        <div className="users-list-container">
          <h3>Existing Users</h3>
          
          {loading && !users.length ? (
            <p className="loading-text">Loading users...</p>
          ) : users.length === 0 ? (
            <p className="no-data">No users found.</p>
          ) : (
            <table className="users-table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Role</th>
                  <th>Description</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr key={user.id}>
                    <td>{user.username}</td>
                    <td>
                      <span className={`role-badge role-${user.role}`}>
                        {user.role}
                      </span>
                    </td>
                    <td>{user.description}</td>
                    <td className="action-buttons">
                      <button
                        onClick={() => selectUserForEdit(user)}
                        className="edit-btn"
                        title="Edit"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteUser(user.id)}
                        className="delete-btn"
                        title="Delete"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

export default Users;
