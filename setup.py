from setuptools import setup, find_packages

setup(
    name="razorpay-ipn-django-handler",
    version="0.1.0",
    description="A Django app for handling Razorpay Instant Payment Notifications (IPN) in webhooks.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/razorpay-ipn-django-handler",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    install_requires=[
        "django>=3.2",  # Adjust based on the minimum Django version you support
        "djangorestframework",  # List other dependencies if any
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",  # Update based on your license
        "Programming Language :: Python :: 3",
        "Framework :: Django",
        "Framework :: Django :: 3.2",  # Specify supported Django versions
    ],
    python_requires=">=3.7",
)