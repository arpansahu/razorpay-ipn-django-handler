from setuptools import setup, find_packages

setup(
    name="razorpay-ipn-django-handler",
    version="1.1.0",
    description="A Django app for handling Razorpay Instant Payment Notifications (IPN) in webhooks.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Arpan Sahu",
    author_email="arpanrocks95@gmail.com",
    url="https://github.com/arpansahu/razorpay-ipn-django-handler",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    install_requires=[
        "Django>=5.2,<6.1",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 5",
        "Framework :: Django :: 5.2",
        "Framework :: Django :: 6",
        "Framework :: Django :: 6.0",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",  # Update based on your license
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.10",
)
