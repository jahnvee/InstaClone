from clarifai.rest import ClarifaiApp
app = ClarifaiApp(api_key='bf44b536a5b24b6e818a246e24051bc2')


model = app.models.get('food-items-v1.0')
response = model.predict_by_url(url='https://www.elementstark.com/woocommerce-extension-demos/wp-content/uploads/sites/2/2016/12/pizza.jpg')
print response
