package com.nicky7x.riptidemaplab;
import org.junit.Test;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import static org.junit.Assert.*;

public class TexturePreviewTest {
    @Test public void parsesConfirmedEtc1AndDxt5Headers() throws Exception {
        byte[] etc=new byte[70+32]; ByteBuffer b=ByteBuffer.wrap(etc).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(21,8);b.putInt(25,8);b.putInt(29,1);b.putInt(33,0x8d64);
        assertEquals(8,TexturePreview.header(etc).width);
        assertEquals(0x8d64,TexturePreview.header(etc).format);
        byte[] dxt=new byte[70+16];
        ByteBuffer v=ByteBuffer.wrap(dxt).order(ByteOrder.LITTLE_ENDIAN);
        v.putInt(21,4);v.putInt(25,4);v.putInt(29,1);v.putInt(33,0x83f3);
        assertEquals(4,TexturePreview.header(dxt).height);
        assertEquals(0x83f3,TexturePreview.header(dxt).format);
        v.putInt(33,0xdead);
        try{TexturePreview.header(dxt);fail("Unknown format accepted");}
        catch(IOException expected){}
    }
    @Test public void decodesKnownBC3Block() throws Exception{
        byte[] bc3=new byte[16];bc3[0]=(byte)255;bc3[1]=0;
        bc3[8]=(byte)0x00;bc3[9]=(byte)0xf8; // red RGB565 endpoint
        bc3[10]=0;bc3[11]=0;
        int[] result=new int[16];TexturePreview.decodeBC3(bc3,0,4,4,result);
        assertEquals(0xffff0000,result[0]);
        assertEquals(0xffff0000,result[15]);
    }
    @Test public void extractsDiffuseImageByActualMaterialParameter(){
        byte[] b=("DiffuseColor\0"+new String(new char[17]).replace('\0','x')+
          "DiffuseTexture\0\0\0\0\0Building/City/ComD_Solid\0").getBytes(StandardCharsets.US_ASCII);
        assertEquals("Building/City/ComD_Solid",TexturePreview.diffuseReference(b));
    }
    @Test public void mapsDocumentedUVOffsets(){
        assertEquals(12,VisualPreviewMeta.uvOffset(20));
        assertEquals(16,VisualPreviewMeta.uvOffset(24));
        assertEquals(16,VisualPreviewMeta.uvOffset(28));
        assertEquals(20,VisualPreviewMeta.uvOffset(32));
        assertEquals(24,VisualPreviewMeta.uvOffset(36));
        assertEquals(-1,VisualPreviewMeta.uvOffset(48));
    }
}
