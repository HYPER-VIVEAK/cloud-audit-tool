import axios from 'axios'

const fallbackBaseURL = `${window.location.protocol}//${window.location.hostname}:8000/api`
const baseURL = import.meta.env.VITE_API_BASE_URL ?? fallbackBaseURL

export const api = axios.create({
  baseURL,
  withCredentials: true,
})

export const resolvedApiBaseUrl = baseURL
