import qrcode
qrimage = qrcode.make("http://gerlachwedding.com/1yr.html")
qrimage.save("qr.jpg","JPEG")