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
}