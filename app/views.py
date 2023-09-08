from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import authenticate, logout,get_user_model,login
from .models import Courses, LearningPath
from rest_framework.views import APIView
from rest_framework import status
import openai , pdb, json, html
import sseclient, time
from rest_framework_simplejwt.tokens import AccessToken
from django.http import JsonResponse,HttpResponse
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializer import  UserSerializer, CourseSerializer, LearningPathSerializer

User = get_user_model()


def index(request):
    return render(request,'index.html')

def loging(request):
    inavlid = None
    if request.method == "POST":
        name = request.POST.get('username')
        passw = request.POST.get('password')
        user = authenticate(username=name, password=passw)
        print(user)


        if user is not None:
            access_token = AccessToken.for_user(user)

            #print(user.id)
            user_data = {
            'id': user.id,
            'username': user.username,
            }
            request.session['user'] = user_data
            
            
            login(request, user)
            print("credential found")
            return redirect('/users', access_token=str(access_token))
            
        else:
            invalid = 'Credential Not Found.Try Again.'
            messages.error(request, invalid)
            return redirect("/login")
    
    print("Render")
    return render(request,'login.html')

@api_view(['POST'])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'User created successfully', 'redirect_url': '/users'}, status=201)

    else:
        return Response({'message': 'invalid Credential. Enter Again'}, status=400)
    

@api_view(['GET'])
def viewsignup(request):
    return render(request, 'signup.html')

@api_view(['GET'])
def viewuser(request):
    user = User.objects.all()
    serializer = UserSerializer(user, many=True)
    return Response(serializer.data)

def userauth(request):
    if request.user.is_authenticated:
        recommended_learning_paths = request.session.get('recommended_learning_paths')
        access_token = request.session.get('access_token') 

        context = {
            'recommended_learning_paths': recommended_learning_paths,
            'access_token': access_token,
        }
        print("auth")
        return render(request, 'user.html', context)
    else:
        print("unautherized")
        return redirect("/login")

@api_view(['GET'])
@permission_classes([IsAuthenticated])  
def pages(request):
    paths = LearningPath.objects.filter(user=request.user)
    learning_paths = LearningPathSerializer(paths, many=True).data

    course_id_to_title = {}
    for course in Courses.objects.all():
        course_id_to_title[course.id] = course.title
    
        
    modified_learning_paths = []
    data = []
    for index, path in enumerate(learning_paths):
        path['course_titles'] = [course_id_to_title.get(course_id, f"Course {course_id}") for course_id in path['course']]
        path_data = LearningPathSerializer(data=path)  # Pass the path data to the serializer
        path_data.is_valid()  # Validate the data
        path_data.validated_data['index'] = index + 1
        path_data.validated_data['course_titles'] = path['course_titles'] 
        modified_learning_paths.append(path_data.validated_data)

    for path_data in modified_learning_paths:
        data.append({
            'index': path_data['index'],
            'title': path_data['course_titles'],  # Assuming you have a 'title' field in the serializer
            'recommended_path': path_data['recommended_path'],
        })

    request.session['modified_learning_paths'] = data
    context = {
        'paths': modified_learning_paths,
        'course_id_to_title': course_id_to_title
    }
    print("auth")
    return render(request, 'pages.html', context)

def logoutuser(request):
    logout(request)
    return redirect("/login")



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request,path_id):

    data = request.session.get('modified_learning_paths') 

    if data:
        for path_data in data:
            if path_data['index'] == path_id:
                course_titles = path_data['title']
                result = path_data['recommended_path']
                recommended_path = result.replace("\n", "")
                print(recommended_path)
                context = {
                    'course_titles': course_titles,
                    'recommended_path': recommended_path
                }
                
                
                return render(request, 'profile.html', context, content_type='text/html')
        
        # If no path data matches the provided path_id
        return HttpResponse("No data found for the specified path_id.")
    else:
        # Handle the case when data is not available in the session
        return HttpResponse("No data found in session.")




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def save(request):
    recommended_learning_paths = request.session.get('recommended_learning_paths')
    course_id= request.session.get('course_id')
    duration= request.session.get('duration')
    user = request.session.get('user')
    serialized_learning_paths = json.dumps(recommended_learning_paths)
    user = request.user

    if course_id is None:
        print("Invalid course_id in session.")
        return redirect('/users')

    
    try:
        course = Courses.objects.get(pk=course_id)
    except Courses.DoesNotExist:
        # Handle the case when the course_id does not exist in the database
        print("Course with the given course_id does not exist.")
        course = None
    
    
    path_data = {
    'user': user.id,
    'course': [course.id] if course else [],
    'recommended_path': serialized_learning_paths,
    }

    path_serializer = LearningPathSerializer(data=path_data)

    if path_serializer.is_valid():

        path_serializer.save()
        print("Path saved successfully.")
    else:
        print("Path serializer validation failed.")
        print(path_serializer.errors)

    return redirect('/pages')


class RecommendedLearningPathsView(APIView):
        
    def post(self, request):
        openai.api_key = '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'

        duration = request.data.get('duration')
        interval = request.data.get('interval')
        technology = request.data.get('technology')
        experience = request.data.get('experience')

        course_data = {
            'duration': duration,
            'interval': interval,
            'title': technology,
            'experience': experience,
        }
        print(duration)
        request.session['duration'] = duration
        
        course_serializer = CourseSerializer(data=course_data)

        if course_serializer.is_valid():    
            course = course_serializer.save()
           
            existing_course = Courses.objects.filter(title=course).first()

            if existing_course:
                # If the course with the same title already exists, use its ID
                course_id = existing_course.id
                print(course_id)
                request.session['course_id'] = course_id
                print(f"Course with title '{course.title}' already exists. Using its ID: {course_id}")
            else:
                # If the course is newly created, use its ID from the serializer
                course_id = course.id
                print(f"New course with title '{course.title}' created. Using its ID: {course_id}")

            # Store the course_id in the session
            
            
            print("Course saved successfully.")
        else:
            print("Course serializer validation failed.")
            print(course_serializer.errors)


        msg = [
            {
                'role': 'user',
                'content': f'Give me learning path for given instructions of {course_data} and the response should be in div of html with appropirate html response format'
            }
        ]


        try:
            time.sleep(1)

            response = openai.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages= msg,
                temperature=0,
            )

            recommended_learning_paths  = response['choices'][0]['message']['content']
            
            request.session['recommended_learning_paths'] = recommended_learning_paths
            print(recommended_learning_paths)
            return HttpResponse( recommended_learning_paths,content_type='text/html')

        except Exception as e:
            return Response({'error': 'Failed to fetch recommended learning paths'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

