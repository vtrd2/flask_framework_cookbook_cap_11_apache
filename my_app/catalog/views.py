from flask import request, jsonify, Blueprint, render_template, flash, redirect, url_for, g, abort
from decimal import Decimal
from my_app.catalog.models import *
from functools import wraps
from my_app import app
from sqlalchemy.orm.util import join
import os
from werkzeug.utils import secure_filename
from my_app import babel, ALLOWED_EXTENSIONS, ALLOWED_LANGUAGES
from flask_babel import lazy_gettext as _
from flask import url_for as flask_url_for

catalog = Blueprint('catalog', __name__)

def allowed_file(filename):
    return '.' in filename and filename.lower().rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def template_or_json(template=None):
    def decorated(f):
        @wraps(f)
        def decorated_fn(*args, **kwargs):
            ctx = f(*args, **kwargs)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or not template:
                return jsonify(ctx)
            else:
                return render_template(template, **ctx)
        return decorated_fn 
    return decorated

@app.before_request
def before():
    if request.view_args and 'lang' in request.view_args:
        g.current_lang = request.view_args['lang']
        request.view_args.pop('lang')

@app.context_processor
def inject_url_for():
    return {
        'url_for': lambda endpoint, **kwargs: flask_url_for(
            endpoint, lang=g.get('current_lang', 'en'), **kwargs
        )
    }

url_for = inject_url_for()['url_for']

@babel.localeselector
def get_locale():
    # print(g.get('current_lang'))
    # return g.get('current_lang', 'fr')
    default_language = 'en'
    language = g.get('current_lang', default_language)
    language = language if language in ALLOWED_LANGUAGES.keys() else default_language
    return language
    # g.get('current_lang', 'en')#request.accept_languages.best_match(ALLOWED_LANGUAGES.keys())

@app.errorhandler(404)
def page_not_found(e):
    app.logger.error(e)
    return render_template('404.html'), 404

@catalog.route('/<lang>/')
@catalog.route('/<lang>/home')
@template_or_json('home.html')
def home():
    products = Product.query.all()
    app.logger.info(
        f'Home page with total of {len(products)} products'
    )
    return {'count': len(products)}

@catalog.route('/<lang>/product/<id>')
def product(id):
    product = Product.query.filter_by(id=id).first()
    if not product:
        app.logger.warning('Requested product not found.')
        abort(404)
    return render_template('product.html', product=product)

@catalog.route('/<lang>/product-create', methods=['POST','GET'])
def create_product():
    form = ProductForm()

    if form.validate_on_submit():
        name = form.name.data
        price = form.price.data
        category = Category.query.get_or_404(form.category.data)
        image = request.files and request.files['image']
        filename = ''
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        product = Product(name, price, category, filename)
        db.session.add(product)
        db.session.commit()
        flash(_('The product %(name)s has been created', name=name),  'success')
        return redirect(url_for('catalog.product', id=product.id))
    
    if form.errors:
        flash(form.errors, 'danger')

    return render_template('product-create.html', form=form)

@catalog.route('/<lang>/category-create', methods=['GET',  'POST'])
def create_category():
    form = CategoryForm()

    if form.validate_on_submit():
        name = form.name.data
        category = Category(name)
        db.session.add(category)
        db.session.commit()
        flash(f'The category {name} has been created', 'success')
        return redirect(url_for('catalog.category', id=category.id))
    
    if form.errors:
        flash(form.errors, 'danger')

    return render_template('category-create.html', form=form)

@catalog.route('/<lang>/categories')
def categories():
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)

@catalog.route('/<lang>/products')
@catalog.route('/<lang>/products/<int:page>')
def products(page=1):
    # import pdb; pdb.set_trace()
    products = Product.query.paginate(page, 10)
    return render_template('products.html', products=products)

@catalog.route('/<lang>/category/<id>')
def category(id):
    category = Category.query.get_or_404(id)
    return render_template('category.html', category=category)

@catalog.route('/<lang>/product-search')
@catalog.route('/<lang>/product-search/<int:page>')
def product_search(page=1):
    name = request.args.get('name')
    price = request.args.get('price')
    company = request.args.get('company')
    category = request.args.get('category')
    products = Product.query
    if name:
        products = products.filter(Product.name.like(f'%{name}%'))
    if price:
        products = products.filter(Product.price == price)
    if company:
        products = products.filter(Product.company.like(f'%{company}%'))
    if category:
        products = products.select_from(join(Product, Category)).filter(
            Category.name.like(f'%{category}%')
        )
    return render_template(
        'products.html', products=products.paginate(page, 10)
    )