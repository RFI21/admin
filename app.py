from flask import Flask, render_template, request, jsonify,redirect,url_for
from bson import ObjectId
from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import hashlib

client = MongoClient('')
db = client.dbresellerida

app=Flask(__name__)
 
@app.route('/', methods=['GET'])
def home():
    data=list(db.produk.find({}))
    return render_template('dashboard.html', data=data)

@app.route('/produk', methods=['GET','POST'])
def produk():
    data=list(db.produk.find({}))
    return render_template('produk.html', data=data)

 
@app.route('/add', methods=['GET','POST'])
def addproduk():
    if request.method == 'POST':
        nama= request.form['nama']
        harga=request.form['harga']
        deskripsi= request.form['deskripsi']
        gambar= request.files['gambar']

        if gambar:
            today = datetime.now()
            mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
            gambar_asli=gambar.filename
            file_gambar=gambar_asli.split('.')[-1]
            file_path=f"static/assets/ImagePath/{mytime}.{file_gambar}"
            gambar.save(file_path)
        else:
            gambar=None
        
        doc = {
            'nama':nama,
            'harga':harga,
            'gambar':file_gambar,
            'deskripsi':deskripsi
        }
        db.produk.insert_one(doc)
        return redirect(url_for('produk',message="Data Berhasil Ditambahkan"))
    return render_template('addProduk.html')

@app.route('/edit', methods=['GET','POST'])
def editproduk():
    # if request.method == 'POST':
    #     id = request.form['_id']
    #     nama = request.form['nama']
    #     harga = request.form['harga']
    #     deskripsi = request.form['deskripsi']
    #     gambar = request.files['gambar']

    #     doc = {
    #         'nama':nama,
    #         'harga':harga,
    #         'deskripsi':deskripsi
    #     }
    #     if gambar:
    #         today = datetime.now()
    #         mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
    #         gambar_asli=gambar.filename
    #         file_gambar=gambar_asli.split('.')[-1]
    #         file_path=f"static/assets/ImagePath/{mytime}.{file_gambar}"
    #         gambar.save(file_path)
    #         doc['gambar']=file_gambar
    #     db.pesanan.update_one({'_id':ObjectId(id)}, {'$set':doc})
    #     return redirect(url_for('produk',message="Data Berhasil Diubah"))

    # id=ObjectId(_id)
    # data=list(db.pesanan.find({'_id':id}))
    return render_template('EditProduk.html')
 
@app.route('/delete/<_id>', methods=['GET','POST'])
def deletefruit(_id):
    db.pesanan.delete_one({'_id':ObjectId(_id)})
    return redirect(url_for('produk',message="Data Berhasil Dihapus"))

@app.route('/pembayaran', methods=['GET','POST'])
def pembayaran():

    return render_template('pembayaran.html')


@app.route('/status', methods=['GET','POST'])
def status():

    return render_template('status.html')

if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug= True)