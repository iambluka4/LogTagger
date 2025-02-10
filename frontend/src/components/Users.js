import React, { useEffect, useState } from 'react';
import { getUsers, createUser, deleteUser } from '../services/api';

function Users() {
  const [users, setUsers] = useState([]);
  const [username, setUsername] = useState("");
  const [description, setDescription] = useState("");

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const res = await getUsers();
      setUsers(res.data);
    } catch (error) {
      console.log("Error fetching users:", error);
    }
  };

  const handleCreateUser = async () => {
    try {
      await createUser({ username, description });
      alert("User created");
      setUsername("");
      setDescription("");
      fetchUsers();
    } catch (error) {
      console.log("Error creating user:", error);
    }
  };

  const handleDeleteUser = async (id) => {
    if (!window.confirm("Are you sure you want to delete this user?")) return;
    try {
      await deleteUser(id);
      alert("User deleted");
      fetchUsers();
    } catch (error) {
      console.log("Error deleting user:", error);
    }
  };

  return (
    <div>
      <h2>Users Management</h2>
      <h4>Create New User</h4>
      <label>Username:</label><br/>
      <input value={username} onChange={e => setUsername(e.target.value)} /><br/>
      <label>Description:</label><br/>
      <input value={description} onChange={e => setDescription(e.target.value)} /><br/>
      <button onClick={handleCreateUser}>Create User</button>

      <hr/>
      <h4>Existing Users</h4>
      <ul>
        {users.map(u => (
          <li key={u.id}>
            {u.username} - {u.description}
            {" "}
            <button onClick={() => handleDeleteUser(u.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Users;
