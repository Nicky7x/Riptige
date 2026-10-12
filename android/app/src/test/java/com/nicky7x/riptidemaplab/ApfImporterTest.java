package com.nicky7x.riptidemaplab;
import org.junit.Test;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.Arrays;
import java.util.zip.DeflaterOutputStream;
import static org.junit.Assert.*;

public class ApfImporterTest {
    private byte[] mesh(){
        ByteBuffer b=ByteBuffer.allocate(4+3*16+4+6+2).order(ByteOrder.LITTLE_ENDIAN);
        b.putInt(3);
        for(int i=0;i<3;i++) { b.putFloat(i);b.putFloat(i+2);b.putFloat(i+5);b.putFloat(0); }
        b.putInt(3);b.putShort((short)0);b.putShort((short)1);b.putShort((short)2);b.put(new byte[]{23,42});
        return b.array();
    }
    @Test public void recognizesMeshAndPreservesTrailingBytes() throws Exception {
        assertArrayEquals(new int[]{3,1},ApfImporter.checkMesh(mesh()));
    }
    @Test public void zlibPayloadIsDecodedLosslessly() throws Exception {
        byte[] raw=mesh();ByteArrayOutputStream out=new ByteArrayOutputStream();
        try(DeflaterOutputStream zip=new DeflaterOutputStream(out)) {zip.write(raw);}
        assertArrayEquals(raw,ApfImporter.unpack(out.toByteArray(),raw.length,1<<16));
    }
    @Test(expected=java.io.IOException.class) public void rejectsInvalidIndices() throws Exception {
        byte[] raw=mesh();ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN).putShort(4+3*16+4,(short)5);
        ApfImporter.checkMesh(raw);
    }
    @Test(expected=java.io.IOException.class) public void rejectsUnknownCodec() throws Exception {
        ApfImporter.unpack(new byte[]{1,2,3},100,5<<16);
    }
    private byte[] visualFixture() throws Exception {
        ByteBuffer b=ByteBuffer.allocate(46+4+9+4+48+8+8+60+4+6+1).order(ByteOrder.LITTLE_ENDIAN);
        b.putFloat(10f).putFloat(50f).putFloat(200f);
        b.position(46);b.putInt(1);b.put("AR/RampA".getBytes("UTF-8"));b.put((byte)0);
        b.putInt(1); // group count
        b.putInt(0).putInt(0).putInt(0).putInt(1); // stream, material, first index, triangles
        b.putFloat(-1).putFloat(-1).putFloat(-1).putFloat(0);
        b.putFloat( 1).putFloat( 1).putFloat( 1).putFloat(0);
        b.putInt(0).putInt(1); // unknown, number of vertex streams
        b.putInt(20).putInt(60); // vertex stride and data length
        for(int i=0;i<3;i++){
            b.putFloat(i).putFloat(i+1).putFloat(i+2).putFloat(0.5f).putFloat(0.5f);
        }
        b.putInt(3).putShort((short)0).putShort((short)1).putShort((short)2).put((byte)0);
        return b.array();
    }
    @Test public void readsVisualModelGeometry() throws Exception {
        byte[] preview=ApfImporter.makeVisualPreview(visualFixture());
        assertArrayEquals(new int[]{3,1},ApfImporter.checkMesh(preview));
        ByteBuffer b=ByteBuffer.wrap(preview).order(ByteOrder.LITTLE_ENDIAN);
        assertEquals(0f,b.getFloat(4),0f);
        assertEquals(1f,b.getFloat(8),0f);
        assertEquals(2f,b.getFloat(12),0f);
    }
    @Test(expected=java.io.IOException.class) public void refusesBrokenVisualMesh() throws Exception {
        byte[] broken=visualFixture(); broken[broken.length-1]=(byte)7;
        ApfImporter.makeVisualPreview(broken);
    }

}