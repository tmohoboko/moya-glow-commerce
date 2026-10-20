import {useCallback,useEffect,useRef,useState} from 'react';
import {api} from './api';

// Postgres + HttpOnly cookie are authoritative. React holds only a UI snapshot.
export function useAccountSession(){
 const [state,setState]=useState({status:'checking',user:null,message:''});
 const pending=useRef(null);
 const refresh=useCallback(async()=>{
  pending.current?.abort();
  const controller=new AbortController();pending.current=controller;
  setState({status:'checking',user:null,message:''});
  try{
   const user=await api('/api/auth/me',{signal:controller.signal});
   if(!controller.signal.aborted)setState({status:'authenticated',user,message:''});
  }catch(error){
   if(!controller.signal.aborted)setState({status:error.status===401?'anonymous':'unavailable',user:null,message:error.status===401?'':error.message});
  }
 },[]);
 const setUser=useCallback(user=>{
  // A stale session lookup must never overwrite a newer login/logout result.
  pending.current?.abort();
  setState({status:user?'authenticated':'anonymous',user,message:''});
 },[]);
 useEffect(()=>{refresh();return()=>pending.current?.abort()},[refresh]);
 return {...state,refresh,setUser};
}
