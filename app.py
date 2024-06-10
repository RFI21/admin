from flask import Flask, render_template, request, jsonify,redirect,url_for,make_response, flash
from bson import ObjectId
from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import hashlib

client = MongoClient('mongodb+srv://rfi:senku27@cluster0.djattxa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client.dbreseller

SECRET_KEY = 'IDA'


app=Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    token_receive = request.cookies.get("ida")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({'username': payload["id"]})
        return render_template('dashboard.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        msg = 'Your token has expired'
        return redirect(url_for('login', msg=msg))
    except jwt.exceptions.DecodeError:
        msg = 'There was a problem logging you in'
        return redirect(url_for('login', msg=msg))

# SIGN IN

@app.route("/sign_in", methods=["POST"])
def sign_in():
    # Sign in
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    result = db.users.find_one(
        {
            "username": username_receive,
            "password": pw_hash,
        }
    )
    if result:
        payload = {
            "id": username_receive,
            # the token will be valid for 24 hours
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify(
            {
                "result": "success",
                "token": token,
            }
        )
    # Let's also handle the case where the id and
    # password combination cannot be found
    else:
        return jsonify(
            {
                "result": "fail",
                "msg": "Kami tidak menemukan pengguna dengan Username/Password tersebut",
            }
        )

@app.route('/login', methods=['GET'])
def login():
    msg = request.args.get('msg')
    return render_template('login.html', msg=msg)


# =========================================================================================================================

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