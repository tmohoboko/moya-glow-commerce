export async function api(path,options={}){
 const response=await fetch(path,{credentials:'same-origin',...options,headers:{'Content-Type':'application/json',...options.headers}});
 let body=null;
 if(response.status!==204){try{body=await response.json()}catch{throw new Error('The account service is unavailable. Please try again shortly.')}}
 if(!response.ok){const error=new Error(typeof body?.detail==='string'?body.detail:'Please try again shortly.');error.status=response.status;throw error}
 return body;
}
