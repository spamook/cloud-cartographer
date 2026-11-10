import PropTypes from 'prop-types'
import React from 'react'

const Errors = ({ errors }) => (
  <div>
    {errors.map((error) => (
      <li key={error} className='errors'>
        {error}
      </li>
    ))}
  </div>
)

Errors.displayName = 'Errors'
Errors.propTypes = {
  errors: PropTypes.arrayOf(PropTypes.string).isRequired,
}

export default Errors
