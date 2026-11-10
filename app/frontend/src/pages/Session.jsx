import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Endpoints } from '../api'
import Errors from '../components/Errors'
import { deleteCookie } from '../utils'

const Session = () => {
  const [user, setUser] = useState(null)
  const [isFetching, setIsFetching] = useState(false)
  const [errors, setErrors] = useState([])
  const navigate = useNavigate()

  const headers = {
    Accept: 'application/json',
    Authorization: document.cookie.split('token=')[1],
  }

  const getUserInfo = async () => {
    try {
      setIsFetching(true)
      const res = await fetch(Endpoints.session, {
        method: 'GET',
        credentials: 'include',
        headers,
      })

      if (!res.ok) {
        logout()
        return
      }

      const { success, errors = [], user } = await res.json()
      setErrors(errors)
      if (!success) navigate('/login')
      setUser(user)
    } catch (e) {
      setErrors([e.toString()])
    } finally {
      setIsFetching(false)
    }
  }

  const logout = async () => {
    const res = await fetch(Endpoints.logout, {
      method: 'GET',
      credentials: 'include',
      headers,
    })

    if (res.ok) {
      deleteCookie('token')
      navigate('/login')
    }
  }

  useEffect(() => {
    getUserInfo()
  }, [])
  return (
    <div className='wrapper'>
      <div>
        {isFetching ? (
          <div>fetching details...</div>
        ) : (
          <div>
            {user && (
              <div>
                <h1>Welcome, {user && user.name}</h1>
                <p>{user && user.email}</p>
                <br />
                <button onClick={logout}>logout</button>
              </div>
            )}
          </div>
        )}

        <Errors errors={errors} />
      </div>
    </div>
  )
}

export default Session
