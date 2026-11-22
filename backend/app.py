"""NutriTrack Flask API. Demo-first implementation; replace mock recognition with a model later."""
import os, io, csv, json, random
from datetime import datetime, date, timedelta
from functools import wraps
from flask import Flask, request, jsonify, g, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-change-this-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'nutritrack.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app, resources={r'/api/*': {'origins': os.environ.get('FRONTEND_ORIGIN', '*')}})
db = SQLAlchemy(app)

class User(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(100), nullable=False); email=db.Column(db.String(160), unique=True, nullable=False, index=True); password_hash=db.Column(db.String(255), nullable=False)
    age=db.Column(db.Integer, default=25); gender=db.Column(db.String(30), default='Prefer not to say'); height_cm=db.Column(db.Float, default=170); weight_kg=db.Column(db.Float, default=70); activity_level=db.Column(db.String(30), default='moderate'); goal=db.Column(db.String(20), default='maintain'); preferences=db.Column(db.Text, default='[]'); restrictions=db.Column(db.Text, default='[]'); created_at=db.Column(db.DateTime, default=datetime.utcnow)
class Food(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(120), unique=True, nullable=False, index=True); calories=db.Column(db.Float, nullable=False); protein=db.Column(db.Float, default=0); carbs=db.Column(db.Float, default=0); fat=db.Column(db.Float, default=0); fibre=db.Column(db.Float, default=0); serving_size=db.Column(db.String(80), default='100 g'); category=db.Column(db.String(50), default='General')
class MealLog(db.Model):
    id=db.Column(db.Integer, primary_key=True); user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True); food_id=db.Column(db.Integer, db.ForeignKey('food.id')); food_name=db.Column(db.String(120), nullable=False); meal_type=db.Column(db.String(20), default='lunch'); quantity=db.Column(db.Float, default=1); calories=db.Column(db.Float, default=0); protein=db.Column(db.Float, default=0); carbs=db.Column(db.Float, default=0); fat=db.Column(db.Float, default=0); fibre=db.Column(db.Float, default=0); logged_at=db.Column(db.DateTime, default=datetime.utcnow, index=True); notes=db.Column(db.String(255), default='')
class Goal(db.Model):
    id=db.Column(db.Integer, primary_key=True); user_id=db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False); calories=db.Column(db.Integer, default=2000); protein=db.Column(db.Float, default=100); carbs=db.Column(db.Float, default=250); fat=db.Column(db.Float, default=67); water_ml=db.Column(db.Integer, default=2000)
class MealPlan(db.Model):
    id=db.Column(db.Integer, primary_key=True); user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True); plan_date=db.Column(db.Date, default=date.today); title=db.Column(db.String(120), default='Daily plan'); meals_json=db.Column(db.Text, nullable=False); created_at=db.Column(db.DateTime, default=datetime.utcnow)
class WeightLog(db.Model):
    id=db.Column(db.Integer, primary_key=True); user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True); weight_kg=db.Column(db.Float, nullable=False); logged_on=db.Column(db.Date, default=date.today)

FOODS=[
('Ugali',360,7,79,2,2,'250 g serving','Kenyan'),('Sukuma wiki',65,3,9,2,4,'150 g serving','Kenyan'),('Githeri',170,7,30,2,7,'200 g serving','Kenyan'),('Chapati',300,6,48,9,3,'1 medium','Kenyan'),('Nyama choma',290,27,0,20,0,'150 g serving','Kenyan'),('Mandazi',270,5,36,11,1,'1 piece','Kenyan'),('Cassava, boiled',160,1,38,0,2,'150 g serving','Kenyan'),('Rice and beans',210,8,39,2,6,'200 g serving','Kenyan'),('Pilau',240,7,35,8,2,'200 g serving','Kenyan'),('Omena',220,28,0,12,0,'100 g serving','Kenyan'),('Rice, cooked',130,3,28,0,0.4,'100 g','Grains'),('Chicken breast',165,31,0,4,0,'100 g','Protein'),('Boiled egg',78,6,1,5,0,'1 large','Protein'),('Banana',89,1,23,0,3,'100 g','Fruit'),('Avocado',160,2,9,15,7,'100 g','Fruit'),('Oatmeal',150,5,27,3,4,'1 bowl','Breakfast'),('Greek yogurt',100,10,4,4,0,'170 g','Dairy'),('Apple',52,0,14,0,2,'100 g','Fruit'),('Beans, cooked',127,9,23,1,6,'100 g','Protein'),('Sukuma wiki with beans',120,6,16,3,6,'200 g serving','Kenyan'),('Beef stew',220,22,7,12,1,'150 g serving','Kenyan'),('Sweet potato, boiled',86,2,20,0,3,'100 g','Vegetable'),('Whole wheat bread',247,13,41,4,7,'100 g','Grains'),('Salmon',208,20,0,13,0,'100 g','Protein'),('Mixed salad',45,2,8,1,3,'150 g bowl','Vegetable'),
('Beef pilau',360,18,45,12,3,'250 g serving','Kenyan'),('Chicken pilau',330,20,42,8,3,'250 g serving','Kenyan'),('Mukimo',180,5,35,2,7,'200 g serving','Kenyan'),('Matoke, stewed',210,4,42,4,6,'250 g serving','Kenyan'),('Irio',190,6,35,3,8,'200 g serving','Kenyan'),('Ndengu stew',180,12,30,2,8,'200 g serving','Kenyan'),('Maharagwe ya nazi',240,10,28,10,8,'200 g serving','Kenyan'),('Wali wa nazi',260,5,42,8,1,'200 g serving','Kenyan'),('Kachumbari',35,2,7,0,2,'150 g serving','Kenyan'),('Beef samosa',220,8,22,11,2,'1 medium','Kenyan'),('Roasted maize',160,5,34,2,4,'1 cob','Kenyan'),('Roasted groundnuts',170,7,6,14,3,'30 g serving','Kenyan'),('Kenyan chai with milk and sugar',90,3,14,3,0,'1 cup','Kenyan'),('Ugali, nyama choma and sukuma wiki',650,38,83,24,11,'1 plate','Kenyan Combo'),('Ugali and beef stew',580,31,86,14,10,'1 plate','Kenyan Combo'),('Ugali, sukuma wiki and beans',480,18,88,7,15,'1 plate','Kenyan Combo'),('Chapati and beans',450,18,72,12,12,'1 plate','Kenyan Combo'),('Chapati and ndengu',480,20,72,11,14,'1 plate','Kenyan Combo'),('Rice and chicken stew',520,34,72,11,7,'1 plate','Kenyan Combo'),('Pilau and kachumbari',290,9,44,9,4,'1 plate','Kenyan Combo')]

def token_for(user): return jwt.encode({'sub':str(user.id),'exp':datetime.utcnow()+timedelta(days=7)}, app.config['SECRET_KEY'], algorithm='HS256')
def current_user():
    auth=request.headers.get('Authorization','')
    if not auth.startswith('Bearer '): return None
    try:
        payload=jwt.decode(auth[7:],app.config['SECRET_KEY'],algorithms=['HS256']); return db.session.get(User,int(payload['sub']))
    except Exception: return None
def auth_required(fn):
    @wraps(fn)
    def wrapped(*args,**kwargs):
        user=current_user()
        if not user: return jsonify({'error':'Authentication required or token expired'}),401
        g.user=user
        return fn(*args,**kwargs)
    return wrapped

def food_dict(f): return {'id':f.id,'name':f.name,'calories':f.calories,'protein':f.protein,'carbs':f.carbs,'fat':f.fat,'fibre':f.fibre,'serving_size':f.serving_size,'category':f.category}
def meal_dict(m): return {'id':m.id,'food_id':m.food_id,'food_name':m.food_name,'meal_type':m.meal_type,'quantity':m.quantity,'calories':m.calories,'protein':m.protein,'carbs':m.carbs,'fat':m.fat,'fibre':m.fibre,'logged_at':m.logged_at.isoformat(),'notes':m.notes}
def profile_dict(u): return {'id':u.id,'name':u.name,'email':u.email,'age':u.age,'gender':u.gender,'height_cm':u.height_cm,'weight_kg':u.weight_kg,'activity_level':u.activity_level,'goal':u.goal,'preferences':json.loads(u.preferences or '[]'),'restrictions':json.loads(u.restrictions or '[]')}
def get_goal(uid):
    goal=Goal.query.filter_by(user_id=uid).first()
    if not goal: goal=Goal(user_id=uid); db.session.add(goal); db.session.commit()
    return goal
def goal_dict(x): return {'calories':x.calories,'protein':x.protein,'carbs':x.carbs,'fat':x.fat,'water_ml':x.water_ml}
def totals(uid, start, end):
    rows=MealLog.query.filter(MealLog.user_id==uid,MealLog.logged_at>=start,MealLog.logged_at<end).all()
    return {'calories':round(sum(x.calories for x in rows)),'protein':round(sum(x.protein for x in rows),1),'carbs':round(sum(x.carbs for x in rows),1),'fat':round(sum(x.fat for x in rows),1),'fibre':round(sum(x.fibre for x in rows),1),'meals':[meal_dict(x) for x in rows]}

@app.errorhandler(400)
def bad_request(e): return jsonify({'error':'Invalid request','details':str(e)}),400
@app.errorhandler(404)
def not_found(e): return jsonify({'error':'Resource not found'}),404
@app.errorhandler(500)
def server_error(e): db.session.rollback(); return jsonify({'error':'Internal server error'}),500
@app.get('/api/health')
def health(): return jsonify({'status':'ok','app':'NutriTrack'})
@app.post('/api/auth/register')
def register():
    d=request.get_json(silent=True) or {}; required=['name','email','password']
    if any(not str(d.get(k,'')).strip() for k in required): return jsonify({'error':'Name, email and password are required'}),400
    email=d['email'].strip().lower()
    if len(d['password'])<8: return jsonify({'error':'Password must be at least 8 characters'}),400
    if User.query.filter_by(email=email).first(): return jsonify({'error':'An account with this email already exists'}),409
    try:
        u=User(name=d['name'].strip(),email=email,password_hash=generate_password_hash(d['password']),age=max(13,int(d.get('age',25))),gender=d.get('gender','Prefer not to say'),height_cm=float(d.get('height_cm',170)),weight_kg=float(d.get('weight_kg',70)),activity_level=d.get('activity_level','moderate'),goal=d.get('goal','maintain'),preferences=json.dumps(d.get('preferences',[])),restrictions=json.dumps(d.get('restrictions',[])))
        db.session.add(u); db.session.flush(); db.session.add(Goal(user_id=u.id,calories=2000,protein=100,carbs=250,fat=67)); db.session.add(WeightLog(user_id=u.id,weight_kg=u.weight_kg)); db.session.commit()
        return jsonify({'token':token_for(u),'user':profile_dict(u)}),201
    except (ValueError,TypeError): db.session.rollback(); return jsonify({'error':'Check that age, height and weight are valid numbers'}),400
@app.post('/api/auth/login')
def login():
    d=request.get_json(silent=True) or {}; u=User.query.filter_by(email=str(d.get('email','')).lower().strip()).first()
    if not u or not check_password_hash(u.password_hash,str(d.get('password',''))): return jsonify({'error':'Email or password is incorrect'}),401
    return jsonify({'token':token_for(u),'user':profile_dict(u)})
@app.get('/api/profile')
@auth_required
def profile(): return jsonify(profile_dict(g.user))
@app.put('/api/profile')
@auth_required
def update_profile():
    d=request.get_json(silent=True) or {}; u=g.user
    for key,col,cast in [('name','name',str),('age','age',int),('gender','gender',str),('height_cm','height_cm',float),('weight_kg','weight_kg',float),('activity_level','activity_level',str),('goal','goal',str)]:
        if key in d:
            try: setattr(u,col,cast(d[key]))
            except (ValueError,TypeError): return jsonify({'error':f'Invalid value for {key}'}),400
    for key in ['preferences','restrictions']:
        if key in d: setattr(u,key,json.dumps(d[key]))
    if 'weight_kg' in d: db.session.add(WeightLog(user_id=u.id,weight_kg=u.weight_kg))
    db.session.commit(); return jsonify(profile_dict(u))
@app.get('/api/foods')
def foods():
    q=request.args.get('search','').strip()
    query=Food.query
    if q: query=query.filter(Food.name.ilike(f'%{q}%'))
    return jsonify([food_dict(x) for x in query.order_by(Food.name).limit(50).all()])
@app.get('/api/foods/<int:food_id>')
def food_detail(food_id):
    f=db.session.get(Food,food_id)
    if not f: return jsonify({'error':'Food not found'}),404
    return jsonify(food_dict(f))
@app.post('/api/recognize')
@auth_required
def recognize():
    if 'image' not in request.files: return jsonify({'error':'Upload an image using the image field'}),400
    image=request.files['image']
    if not image.filename: return jsonify({'error':'Choose an image first'}),400
    if image.mimetype not in ['image/jpeg','image/png','image/webp','image/gif']: return jsonify({'error':'Use a JPG, PNG, WEBP or GIF image'}),400
    # Mock recognition: deliberately transparent, deterministic demo result.
    all_foods=Food.query.order_by(Food.id).all()
    if not all_foods: return jsonify({'error':'Food database is empty'}),503
    f=next((x for x in all_foods if x.name.lower() in ('githeri','ugali','chapati')),all_foods[0])
    return jsonify({'recognizer':'mock','notice':'Demo prediction only; this is not real AI recognition.','food':food_dict(f),'confidence':0.82,'alternatives':[food_dict(x) for x in all_foods if x.id!=f.id][:3]})
@app.route('/api/meals',methods=['GET','POST'])
@auth_required
def meals():
    if request.method=='GET':
        day=request.args.get('date',date.today().isoformat())
        try: d=date.fromisoformat(day)
        except ValueError: return jsonify({'error':'date must use YYYY-MM-DD'}),400
        return jsonify(totals(g.user.id,datetime.combine(d,datetime.min.time()),datetime.combine(d+timedelta(days=1),datetime.min.time())))
    d=request.get_json(silent=True) or {}; f=db.session.get(Food,int(d['food_id'])) if d.get('food_id') else None
    if not f and not d.get('food_name'): return jsonify({'error':'food_id or food_name is required'}),400
    try: qty=float(d.get('quantity',1))
    except (ValueError,TypeError): return jsonify({'error':'quantity must be a number'}),400
    if qty<=0 or qty>100: return jsonify({'error':'quantity must be between 0 and 100'}),400
    base=f or None; factor=qty
    try: logged=datetime.fromisoformat(d.get('logged_at',datetime.now().isoformat()))
    except ValueError: return jsonify({'error':'logged_at must be ISO date/time'}),400
    m=MealLog(user_id=g.user.id,food_id=base.id if base else None,food_name=base.name if base else str(d['food_name'])[:120],meal_type=d.get('meal_type','lunch'),quantity=qty,calories=float(d.get('calories',base.calories if base else 0))*factor,protein=float(d.get('protein',base.protein if base else 0))*factor,carbs=float(d.get('carbs',base.carbs if base else 0))*factor,fat=float(d.get('fat',base.fat if base else 0))*factor,fibre=float(d.get('fibre',base.fibre if base else 0))*factor,logged_at=logged,notes=str(d.get('notes',''))[:255])
    db.session.add(m); db.session.commit(); return jsonify(meal_dict(m)),201
@app.route('/api/meals/<int:meal_id>',methods=['PUT','DELETE'])
@auth_required
def meal_item(meal_id):
    m=MealLog.query.filter_by(id=meal_id,user_id=g.user.id).first_or_404()
    if request.method=='DELETE': db.session.delete(m); db.session.commit(); return jsonify({'success':True})
    d=request.get_json(silent=True) or {}
    for k in ['meal_type','notes']:
        if k in d: setattr(m,k,str(d[k])[:255])
    if 'quantity' in d:
        try: q=float(d['quantity'])
        except (ValueError,TypeError): return jsonify({'error':'quantity must be numeric'}),400
        if q<=0 or q>100: return jsonify({'error':'quantity must be between 0 and 100'}),400
        ratio=q/(m.quantity or 1)
        for k in ['calories','protein','carbs','fat','fibre']: setattr(m,k,getattr(m,k)*ratio)
        m.quantity=q
    db.session.commit(); return jsonify(meal_dict(m))
@app.route('/api/goals',methods=['GET','PUT'])
@auth_required
def goals():
    x=get_goal(g.user.id)
    if request.method=='GET': return jsonify(goal_dict(x))
    d=request.get_json(silent=True) or {}
    for k in ['calories','protein','carbs','fat','water_ml']:
        if k in d:
            try: v=float(d[k])
            except (ValueError,TypeError): return jsonify({'error':f'{k} must be numeric'}),400
            if v<=0 or v>10000: return jsonify({'error':f'{k} is outside the accepted range'}),400
            setattr(x,k,v)
    db.session.commit(); return jsonify(goal_dict(x))
@app.get('/api/progress')
@auth_required
def progress():
    span=request.args.get('range','week'); days=7 if span=='week' else 30 if span=='month' else None
    if not days: return jsonify({'error':'range must be week or month'}),400
    today=date.today(); result=[]
    for i in range(days-1,-1,-1):
        d=today-timedelta(days=i); t=totals(g.user.id,datetime.combine(d,datetime.min.time()),datetime.combine(d+timedelta(days=1),datetime.min.time()))
        result.append({'date':d.isoformat(),'calories':t['calories'],'protein':t['protein'],'carbs':t['carbs'],'fat':t['fat']})
    return jsonify(result)
@app.get('/api/history')
@auth_required
def history():
    q=MealLog.query.filter_by(user_id=g.user.id)
    if request.args.get('from'):
        try: q=q.filter(MealLog.logged_at>=datetime.fromisoformat(request.args['from']))
        except ValueError: return jsonify({'error':'from must be an ISO date'}),400
    if request.args.get('to'):
        try: q=q.filter(MealLog.logged_at<datetime.fromisoformat(request.args['to'])+timedelta(days=1))
        except ValueError: return jsonify({'error':'to must be an ISO date'}),400
    if request.args.get('meal_type'): q=q.filter_by(meal_type=request.args['meal_type'])
    rows=q.order_by(MealLog.logged_at.desc()).limit(1000).all()
    if request.args.get('format')=='csv':
        out=io.StringIO(); w=csv.writer(out); w.writerow(['date','food','meal_type','quantity','calories','protein','carbs','fat'])
        for m in rows: w.writerow([m.logged_at.isoformat(),m.food_name,m.meal_type,m.quantity,m.calories,m.protein,m.carbs,m.fat])
        return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=nutritrack-history.csv'})
    return jsonify([meal_dict(x) for x in rows])
@app.route('/api/mealplan',methods=['GET'])
@auth_required
def get_plan():
    p=MealPlan.query.filter_by(user_id=g.user.id).order_by(MealPlan.created_at.desc()).first()
    return jsonify({'plan':json.loads(p.meals_json),'title':p.title,'date':p.plan_date.isoformat()} if p else {'plan':[],'title':'No saved plan yet','date':date.today().isoformat()})
@app.post('/api/mealplan/generate')
@auth_required
def generate_plan():
    goal=get_goal(g.user.id); all_foods=Food.query.order_by(Food.id).all()
    if not all_foods: return jsonify({'error':'Food database is empty'}),503
    picks={}
    for meal,choices in [('Breakfast',['Oatmeal','Boiled egg','Banana','Greek yogurt']),('Lunch',['Ugali','Sukuma wiki','Githeri','Rice and beans']),('Dinner',['Nyama choma','Pilau','Omena','Sweet potato, boiled']),('Snack',['Apple','Avocado','Mandazi'])]:
        found=[x for x in all_foods if x.name in choices]
        if found:
            f=random.choice(found); picks[meal]={'food':food_dict(f),'quantity':1,'calories':f.calories,'protein':f.protein,'carbs':f.carbs,'fat':f.fat,'fibre':f.fibre}
    p=MealPlan(user_id=g.user.id,plan_date=date.today(),title='Your daily nutrition plan',meals_json=json.dumps(picks)); db.session.add(p); db.session.commit()
    return jsonify({'plan':picks,'title':p.title,'date':p.plan_date.isoformat(),'target_calories':goal.calories,'notice':'Suggestions are general wellness ideas, not medical or dietetic advice.'}),201
@app.post('/api/mealplan/add')
@auth_required
def add_planned_meal():
    d=request.get_json(silent=True) or {}; f=db.session.get(Food,int(d.get('food_id',0)))
    if not f: return jsonify({'error':'Choose a valid food'}),400
    m=MealLog(user_id=g.user.id,food_id=f.id,food_name=f.name,meal_type=d.get('meal_type','lunch'),quantity=1,calories=f.calories,protein=f.protein,carbs=f.carbs,fat=f.fat,fibre=f.fibre,logged_at=datetime.now())
    db.session.add(m); db.session.commit(); return jsonify(meal_dict(m)),201

def seed():
    for row in FOODS:
        if not Food.query.filter_by(name=row[0]).first(): db.session.add(Food(name=row[0],calories=row[1],protein=row[2],carbs=row[3],fat=row[4],fibre=row[5],serving_size=row[6],category=row[7]))
    db.session.commit()
    demo=User.query.filter_by(email='demo@nutritrack.app').first()
    if not demo:
        demo=User(name='Alex Demo',email='demo@nutritrack.app',password_hash=generate_password_hash('NutriTrack123!'),age=24,gender='Prefer not to say',height_cm=168,weight_kg=68,activity_level='moderate',goal='maintain',preferences=json.dumps(['Kenyan food']),restrictions='[]'); db.session.add(demo); db.session.flush(); db.session.add(Goal(user_id=demo.id,calories=2100,protein=110,carbs=260,fat=70,water_ml=2200)); db.session.add(WeightLog(user_id=demo.id,weight_kg=69.2,logged_on=date.today()-timedelta(days=21))); db.session.add(WeightLog(user_id=demo.id,weight_kg=68.7,logged_on=date.today()-timedelta(days=14))); db.session.add(WeightLog(user_id=demo.id,weight_kg=68.0,logged_on=date.today()-timedelta(days=7)))
        db.session.commit()
        for name,meal,qty,days_ago in [('Oatmeal','breakfast',1,0),('Banana','snack',1,0),('Githeri','lunch',1.2,0),('Sukuma wiki','dinner',1,0),('Chapati','breakfast',1,1),('Beans, cooked','lunch',1,1),('Nyama choma','dinner',1,1),('Greek yogurt','snack',1,2),('Rice and beans','lunch',1,2)]:
            f=Food.query.filter_by(name=name).first(); logged=datetime.combine(date.today()-timedelta(days=days_ago),datetime.min.time())+timedelta(hours={'breakfast':8,'lunch':13,'dinner':19,'snack':16}[meal])
            db.session.add(MealLog(user_id=demo.id,food_id=f.id,food_name=f.name,meal_type=meal,quantity=qty,calories=f.calories*qty,protein=f.protein*qty,carbs=f.carbs*qty,fat=f.fat*qty,fibre=f.fibre*qty,logged_at=logged))
        db.session.commit()
with app.app_context():
    db.create_all(); seed()
if __name__=='__main__': app.run(debug=os.environ.get('FLASK_DEBUG','1')=='1',host='0.0.0.0',port=int(os.environ.get('PORT',5000)))
