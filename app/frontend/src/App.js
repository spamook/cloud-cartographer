import React from 'react'
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom'
import './App.css'
import Login from './pages/Login'
import Register from './pages/Register'
import Session from './pages/Session'

function App() {
  return (
    <Router>
      <Routes>
        <Route exact path="/" element={<Session />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/session" element={<Session />} />
      </Routes>
    </Router>
  )
}

export default App