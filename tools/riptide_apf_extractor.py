#!/usr/bin/env python3
"""
riptide_apf_extractor.py — protótipo fornecido pelo Claude.
Lista e extrai recursos de um Assets.apf ("FPUV" v6).

Uso:
  python tools/riptide_apf_extractor.py info Assets.apf
  python tools/riptide_apf_extractor.py list Assets.apf [filtro]
  python tools/riptide_apf_extractor.py extract Assets.apf SAIDA/ [filtro]
  python tools/riptide_apf_extractor.py json Assets.apf inventario.json

ATENÇÃO: protótipo de leitura sem validações suficientes de paths, limites e
tamanhos; use apenas com seu arquivo original confiável. Não publique extrações.
O suposto CRC e o hash do cabeçalho não foram identificados com segurança.
"""
import json, lzma, os, struct, sys, zlib


def load(path):
    data = open(path, "rb").read()
    if data[:4] != b"FPUV":
        sys.exit("Nao parece um APF 'FPUV'.")
    ver, idx_off, count, idx_size, hsh = struct.unpack("<5I", data[4:24])
    platform = data[24:56].split(b"\0")[0].decode("ascii", "replace")
    idx, p, ents = data[idx_off:idx_off + idx_size], 0, []
    for _ in range(count):
        e = idx.index(b"\0", p)
        name = idx[p:e].decode("utf-8", "replace")
        off, us, cs, crc, fl = struct.unpack("<5I", idx[e + 1:e + 21])
        ents.append(dict(name=name, offset=off, usize=us, csize=cs, crc=crc, flags=fl))
        p = e + 21
    hdr = dict(version=ver, index_offset=idx_off, count=count,
               index_size=idx_size, hash=hsh, platform=platform)
    return data, hdr, ents


def read_resource(data, e):
    raw = data[e["offset"]:e["offset"] + e["csize"]]
    kind = e["flags"] >> 16
    if kind == 0 or e["csize"] == e["usize"]:
        return raw
    if kind == 1:
        return zlib.decompress(raw)
    if kind == 2:
        pr = raw[0]
        ds = struct.unpack("<I", raw[1:5])[0]
        lc, rest = pr % 9, pr // 9
        flt = [dict(id=lzma.FILTER_LZMA1, dict_size=max(ds, 4096),
                    lc=lc, lp=rest % 5, pb=rest // 5)]
        d = lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=flt)
        return d.decompress(raw[5:], max_length=e["usize"])
    raise ValueError("compressao desconhecida: flags=%#x" % e["flags"])


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd, path = sys.argv[1], sys.argv[2]
    data, hdr, ents = load(path)
    if cmd == "info":
        print(json.dumps(hdr, indent=2))
    elif cmd == "list":
        flt = sys.argv[3] if len(sys.argv) > 3 else ""
        for e in ents:
            if flt in e["name"]:
                print("%10d  %s" % (e["usize"], e["name"]))
    elif cmd == "extract":
        out, flt = sys.argv[3], (sys.argv[4] if len(sys.argv) > 4 else "")
        n = 0
        for e in ents:
            if flt not in e["name"]:
                continue
            dest = os.path.join(out, *e["name"].split("/")) + ".bin"
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(read_resource(data, e))
            n += 1
        print("%d recursos extraidos para %s" % (n, out))
    elif cmd == "json":
        json.dump(dict(header=hdr, resources=ents), open(sys.argv[3], "w"), indent=1)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
