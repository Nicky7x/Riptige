package com.nicky7x.riptidemaplab;

import android.graphics.Bitmap;
import android.opengl.ETC1;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;

/** Read-only previews of confirmed APF texture types. Never writes game assets. */
final class TexturePreview {
    private TexturePreview() {}
    static final int GL_ETC1=0x8D64,GL_DXT5=0x83F3,GL_LUMINANCE=0x1909,GL_RGBA=0x1908;
    static final class Header {
        final int width,height,format,levels;
        Header(int w,int h,int f,int l){width=w;height=h;format=f;levels=l;}
    }
    static Header header(byte[] data) throws IOException {
        if(data.length<70)throw new IOException("Textura truncada");
        ByteBuffer b=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        int w=b.getInt(21),h=b.getInt(25),levels=b.getInt(29),format=b.getInt(33);
        if(w<4||h<4||w>2048||h>2048||levels<1||levels>16)
            throw new IOException("Dimensões inválidas da textura");
        long base;
        switch(format){
            case GL_ETC1: base=(long)((w+3)/4)*((h+3)/4)*8;break;
            case GL_DXT5: base=(long)((w+3)/4)*((h+3)/4)*16;break;
            case GL_LUMINANCE:base=(long)w*h;break;
            case GL_RGBA:base=(long)w*h*4;break;
            default:throw new IOException("Formato de textura ainda não suportado: 0x"+Integer.toHexString(format));
        }
        if(base>data.length-70)throw new IOException("Pixels incompletos");
        return new Header(w,h,format,levels);
    }
    static String diffuseReference(byte[] material) {
        byte[] needle="DiffuseTexture\0".getBytes(StandardCharsets.US_ASCII);
        int at=-1;
        for(int i=0;i+needle.length+5<material.length;i++){
            boolean match=true;for(int j=0;j<needle.length;j++)if(material[i+j]!=needle[j]){match=false;break;}
            if(match)at=i;
        }
        if(at<0)return null;
        int p=at+needle.length+4;
        int end=p;
        while(end<material.length&&end-p<256&&material[end]!=0)end++;
        if(end==p||end>=material.length||end-p>=256)return null;
        for(int i=p;i<end;i++)if(material[i]<32||material[i]>126)return null;
        return new String(material,p,end-p,StandardCharsets.US_ASCII);
    }
    /** Image is never stored on public servers. Output PNG limited to 256px per edge. */
    static byte[] png(byte[] resource) throws IOException {
        Header h=header(resource);
        int w=h.width,hg=h.height;
        if((long)w*hg>2048L*2048)throw new IOException("Textura grande demais");
        int[] pixels=new int[w*hg];
        if(h.format==GL_ETC1){
            ByteBuffer src=ByteBuffer.allocateDirect(((w+3)/4)*((hg+3)/4)*8);
            src.put(resource,70,src.capacity());src.position(0);
            ByteBuffer dst=ByteBuffer.allocateDirect(w*hg*3);
            ETC1.decodeImage(src,dst,w,hg,3,w*3);
            dst.position(0);
            for(int i=0;i<pixels.length;i++){
                int r=dst.get()&255,g=dst.get()&255,b=dst.get()&255;
                pixels[i]=0xff000000|(r<<16)|(g<<8)|b;
            }
        }else if(h.format==GL_DXT5){
            decodeBC3(resource,70,w,hg,pixels);
        }else{
            for(int i=0;i<pixels.length;i++){
                int at=70+i*(h.format==GL_RGBA?4:1);
                int r=resource[at]&255,g=h.format==GL_RGBA?(resource[at+1]&255):r;
                int b=h.format==GL_RGBA?(resource[at+2]&255):r;
                int a=h.format==GL_RGBA?(resource[at+3]&255):255;
                pixels[i]=(a<<24)|(r<<16)|(g<<8)|b;
            }
        }
        Bitmap img=Bitmap.createBitmap(pixels,w,hg,Bitmap.Config.ARGB_8888);
        int max=Math.max(w,hg);
        if(max>256){int nw=Math.max(1,Math.round(w*256f/max)),nh=Math.max(1,Math.round(hg*256f/max));
            Bitmap smaller=Bitmap.createScaledBitmap(img,nw,nh,true);img.recycle();img=smaller;
        }
        try{
            ByteArrayOutputStream out=new ByteArrayOutputStream();
            if(!img.compress(Bitmap.CompressFormat.PNG,90,out))throw new IOException("Não foi possível converter PNG");
            return out.toByteArray();
        }finally{img.recycle();}
    }
    /** BC3/DXT5: 16 bytes per 4x4 block; 3-bit alpha + RGB565 endpoints. */
    static void decodeBC3(byte[] bytes,int base,int w,int h,int[] pixels) throws IOException {
        int blocksX=(w+3)/4,blocksY=(h+3)/4;
        for(int by=0;by<blocksY;by++)for(int bx=0;bx<blocksX;bx++){
            int o=base+16*(by*blocksX+bx);
            if(o+16>bytes.length)throw new IOException("Bloco DXT5 incompleto");
            int a0=bytes[o]&255,a1=bytes[o+1]&255;long alphaBits=0;
            for(int k=0;k<6;k++)alphaBits|=((long)bytes[o+2+k]&255)<<(8*k);
            int[] aa=new int[8];aa[0]=a0;aa[1]=a1;
            if(a0>a1){for(int k=1;k<=6;k++)aa[k+1]=((7-k)*a0+k*a1)/7;}
            else{for(int k=1;k<=4;k++)aa[k+1]=((5-k)*a0+k*a1)/5;aa[6]=0;aa[7]=255;}
            int c0=(bytes[o+8]&255)|((bytes[o+9]&255)<<8),c1=(bytes[o+10]&255)|((bytes[o+11]&255)<<8);
            int[] cc=new int[4];cc[0]=rgb565(c0);cc[1]=rgb565(c1);
            cc[2]=mix(cc[0],cc[1],2,1);cc[3]=mix(cc[0],cc[1],1,2);
            int index=(bytes[o+12]&255)|((bytes[o+13]&255)<<8)|((bytes[o+14]&255)<<16)|((bytes[o+15]&255)<<24);
            for(int yy=0;yy<4;yy++)for(int xx=0;xx<4;xx++){
                int pixel=4*yy+xx,x=bx*4+xx,y=by*4+yy;if(x>=w||y>=h)continue;
                int a=aa[(int)((alphaBits>>>(3*pixel))&7)],c=cc[(index>>>(2*pixel))&3];
                pixels[y*w+x]=(a<<24)|c;
            }
        }
    }
    private static int rgb565(int c){int r=(c>>11)&31,g=(c>>5)&63,b=c&31;
        return (((r<<3)|(r>>2))<<16)|(((g<<2)|(g>>4))<<8)|((b<<3)|(b>>2));}
    private static int mix(int c0,int c1,int k0,int k1){int r=(((c0>>16)&255)*k0+((c1>>16)&255)*k1)/3;
        int g=(((c0>>8)&255)*k0+((c1>>8)&255)*k1)/3,b=((c0&255)*k0+(c1&255)*k1)/3;
        return (r<<16)|(g<<8)|b;}
}