import axios from 'axios';
export const api=axios.create({baseURL:import.meta.env.VITE_API_URL||'http://localhost:8000/api/v1',timeout:8000});
api.interceptors.request.use(c=>{const t=localStorage.getItem('fg_token');if(t)c.headers.Authorization=`Bearer ${t}`;return c});
api.interceptors.response.use(r=>r,e=>{if(e.response?.status===401)localStorage.removeItem('fg_token');return Promise.reject(e)});
export async function safeGet<T>(url:string,fallback:T):Promise<T>{try{return (await api.get<T>(url)).data}catch{return fallback}}
