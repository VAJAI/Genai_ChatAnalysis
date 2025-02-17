import React from 'react'
import Image from 'next/image'
import notfound from '../public/gallery/notfound.gif'
import Link from 'next/link'


export default  async function() {
  return (
    <div >
    <div className='not_found'>
       <Image
       src={notfound}
       width={0}
       height={0}
       alt="#"/>
      
      <h2>404 Page Not_Found</h2>
      <p><Link href='/' className="link_home">Go Back Home</Link></p>
       
    </div>
    
    </div>
  )
}
