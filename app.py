from flask import Flask, render_template, request, jsonify,redirect,url_for,make_response, flash
from bson import ObjectId
from pymongo import MongoClient
import jwt
from datetime import datetime, timedelta
import hashlib
from functools import wraps
import babel.numbers

# client = MongoClient('mongodb+srv://rfi:senku27@cluster0.djattxa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
# db = client.dbreseller

client = MongoClient('mongodb+srv://resellerida:idariseller@cluster0.yckjm3g.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client.dbreseller

SECRET_KEY = 'IDA'
TOKEN_KEY = 'ida'

app=Flask(__name__)

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            token_receive = request.cookies.get("ida")
            try:
                payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
                if payload.get("role") != role:
                    return redirect(url_for('login', msg="Unauthorized access"))
                return f(*args, **kwargs)
            except jwt.ExpiredSignatureError:
                return redirect(url_for('login', msg="Your token has expired"))
            except jwt.exceptions.DecodeError:
                return redirect(url_for('login', msg="There was a problem logging you in"))
        return wrapped
    return wrapper

@app.route('/admin')
@role_required('admin')
def admin_page():
    return render_template('admin/dashboard.html')

@app.route('/user')
@role_required('user')
def user_page():
    return render_template('index.html')

@app.route('/', methods=['GET'])
def home():
    token_receive = request.cookies.get("ida")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({'username': payload["id"]})
        role = payload.get("role")
        if role == "admin":
            return render_template('admin/dashboard.html', user_info=user_info)
        elif role == "user":
            data=list(db.produk.find({}))
            for item in data:
                if 'harga' in item:
                    item['harga']=babel.numbers.format_currency(item['harga'], "IDR", locale='id_ID')
            return render_template('index.html', user_info=user_info,data=data)
        else:
            return redirect(url_for('login', msg="Role not recognized"))

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
            "role": result.get("role"),
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

# SIGN UP
@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form.get('username_give')
    password_receive = request.form.get('password_give')
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    if db.users.find_one({"username": username_receive}):
        return jsonify({'result': 'fail', 'msg': 'Username already exists'})


    doc = {
        "username": username_receive,
        "password": password_hash,
        "role": "user"  # setting default role
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})

# CEK ID
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form.get('username_give')
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})

@app.route('/logout', methods=['GET'])
def logout():
    response = make_response(redirect('/login'))
    response.set_cookie(TOKEN_KEY, expires=0)
    return response

@app.route('/login', methods=['GET'])
def login():
    msg = request.args.get('msg')
    return render_template('login.html', msg=msg)


# =========================================================================================================================
# ADMIN PAGE

@app.route('/produk', methods=['GET','POST'])
def produk():
    data=list(db.produk.find({}))
    for item in data:
        if 'harga' in item:
            item['harga']=babel.numbers.format_currency(item['harga'], "IDR", locale='id_ID')
        
    return render_template('admin/produk.html', data=data)


 
@app.route('/add', methods=['GET','POST'])
def addproduk():
    if request.method == 'POST':
        nama= request.form['nama']
        harga=request.form['harga']
        stok= request.form['stok']
        ukuran=request.form.getlist('ukuran')
        deskripsi= request.form['deskripsi']
        gambar= request.files['gambar']

        if gambar:
            today = datetime.now()
            mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
            gambar_asli=gambar.filename
            file_gambar=gambar_asli.split('.')[-1]
            file_asli=f"{mytime}.{file_gambar}"
            file_path=f"static/assets/ImagePath/{mytime}.{file_gambar}"
            gambar.save(file_path)
        else:
            gambar=None
        
        doc = {
            'nama':nama,
            'harga':harga,
            'ukuran':ukuran,
            'stok':stok,
            'gambar':file_asli,
            'deskripsi':deskripsi
        }
        db.produk.insert_one(doc)
        return redirect(url_for('produk',message="Data Berhasil Ditambahkan"))
    return render_template('admin/addProduk.html')

@app.route('/edit/<_id>', methods=['GET','POST'])
def editproduk(_id):
    if request.method == 'POST':
        id = request.form['_id']
        nama= request.form['nama']
        harga=request.form['harga']
        stok= request.form['stok']
        ukuran=request.form.getlist('ukuran')
        deskripsi= request.form['deskripsi']
        gambar= request.files['gambar']


        doc = {
            'nama':nama,
            'harga':harga,
            'ukuran':ukuran,
            'stok':stok,
            'deskripsi':deskripsi
        }
        if gambar:
            today = datetime.now()
            mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
            gambar_asli=gambar.filename
            file_gambar=gambar_asli.split('.')[-1]
            file_asli=f"{mytime}.{file_gambar}"
            file_path=f"static/assets/ImagePath/{mytime}.{file_gambar}"
            gambar.save(file_path)
            doc['gambar']=file_asli
        db.produk.update_one({'_id':ObjectId(id)}, {'$set':doc})
        return redirect(url_for('produk',message="Data Berhasil Diubah"))

    id=ObjectId(_id)
    data=list(db.produk.find({'_id':id}))
    return render_template('admin/EditProduk.html', data=data[0])
 
@app.route('/delete/<_id>', methods=['GET','POST'])
def deleteproduk(_id):
    db.produk.delete_one({'_id':ObjectId(_id)})
    return redirect(url_for('produk',message="Data Berhasil Dihapus"))

@app.route('/pembayaran', methods=['GET','POST'])
def pembayaran():
    orderan=list(db.orderan.find({}))

    return render_template('admin/pembayaran.html',orderan=orderan)


@app.route('/status', methods=['GET','POST'])
def status():
    orderan=list(db.orderan.find({}))

    return render_template('admin/status.html',orderan=orderan)


@app.route('/update_status/<_id>', methods=['POST'])
def update_status(_id):
    new_status = request.form.get('status')
    db.orderan.update_one({'_id': ObjectId(_id)}, {'$set': {'status': new_status}})
    return jsonify({'result': 'success'})

@app.route('/delete_order/<_id>', methods=['GET','POST'])
def deletepesanan(_id):
    db.orderan.delete_one({'_id':ObjectId(_id)})
    return jsonify({'result': 'success'})
# =========================================================================================
# USER PAGE

@app.route('/shop', methods=['GET'])
def shop():
    data=list(db.produk.find({}))
    for item in data:
        if 'harga' in item:
            item['harga']=babel.numbers.format_currency(item['harga'], "IDR", locale='id_ID')
    return render_template('shop.html',data=data)

@app.route('/detail/<_id>', methods=['GET'])
def detail(_id):
    id=ObjectId(_id)
    data=list(db.produk.find({'_id':id}))
    data2=list(db.produk.find({}))
    for item in data:
        if 'harga' in item:
            item['harga']=babel.numbers.format_currency(item['harga'], "IDR", locale='id_ID')
    return render_template('detail.html', produk=data[0],data2=data2)



@app.route('/contact', methods=['GET'])
def contact():
    msg = request.args.get('msg')
    return render_template('contact.html', msg=msg)



@app.route('/checkout/<_id>', methods=['GET','POST'])
def checkout(_id):
    id=ObjectId(_id)

    if request.method == 'POST':
        # Ambil data dari form
        # idpdk = request.form['id']
        kuantitas = request.form['kuantitas']
        ukuran = request.form['ukuran']
        
        # Dapatkan data produk dari database
        product = db.produk.find_one({'_id': id})
        
        # Hitung total harga
        harga = product['harga']
        total_harga = int(harga) * int(kuantitas)
        
        # Konversi mata uang
        hargaAsli=babel.numbers.format_currency(harga, "IDR", locale='id_ID')
        total=babel.numbers.format_currency(total_harga, "IDR", locale='id_ID')

        # Simpan pesanan ke database
        pesanan = {
            'idpdk':product['_id'],
            'nama': product['nama'],
            'kuantitas': kuantitas,
            'ukuran':ukuran,
            'harga':hargaAsli,
            'total_harga': total

        }
        
        db.pesanan.insert_one(pesanan)
        return redirect(url_for('order', order_id=pesanan['_id']))
    
@app.route('/order/<order_id>', methods=['GET'])
def order(order_id):
    id=ObjectId(order_id)
    data=db.pesanan.find_one({'_id':id})

    return render_template('checkout.html', pesanan=data)

@app.route('/batal/<_id>', methods=['GET'])
def batal(_id):
    db.pesanan.delete_one({'_id':ObjectId(_id)})
    return redirect(url_for('shop',message="Pesanan Dibatalkan"))


@app.route('/pesan/<_id>', methods=['POST'])
def pesanan(_id):
        token_receive = request.cookies.get("ida")
        id=ObjectId(_id)

        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            # Dapatkan data produk dari database
            pesanan = db.pesanan.find_one({'_id': id})
            idpdk = pesanan['idpdk']
            print(idpdk)
            produc=db.produk.find_one({'_id': ObjectId(idpdk)})
            # mengambil stok
            stok=int(produc['stok'])
            

            user_info = db.users.find_one({"username": payload["id"]})
            user=user_info['username']

            nama = request.form["namaUser"]
            nomor = request.form["no"]
            alamat = request.form["alamat"]
            gambar = request.files["bukti"]
            namapdk = pesanan['nama']
            kuantitas = pesanan['kuantitas']
            harga = pesanan['harga']
            ukuran =  pesanan['ukuran']
            total = pesanan['total_harga']

            newStok=int(stok)- int(kuantitas)

            if gambar:
                today = datetime.now()
                mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
                gambar_asli=gambar.filename
                file_gambar=gambar_asli.split('.')[-1]
                file_asli=f"{mytime}.{file_gambar}"
                file_path=f"static/assets/ImagePath/Bukti/{user}_{mytime}.{file_gambar}"
                gambar.save(file_path)
            else:
                gambar=None

            doc = {
                "username": user_info["username"],
                "nama": nama,
                "nomor": nomor,
                "alamat": alamat,
                "bukti": file_asli,
                "namapdk": namapdk,
                "harga": harga,
                "kuantitas": kuantitas,
                "ukuran": ukuran,
                "total": total,
                "status":"Di Proses"
            }
            db.orderan.insert_one(doc)
            db.produk.update_one({'_id':idpdk}, {'$set':{'stok':newStok}})
            return redirect(url_for("statusUser", message ="Berhasil melakukan pemesanan"))
        except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
            return redirect(url_for("home"))


@app.route('/statusUser', methods=['GET'])
def statusUser():
    token_receive = request.cookies.get("ida")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        data=list(db.orderan.find({"username": payload["id"]}))
        return render_template('status.html', data=data)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
            return redirect(url_for("home"))

if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug= True)