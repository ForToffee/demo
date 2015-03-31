<div background-color="black">
    <a href="http://iotic-labs.com"><img src="https://github.com/Iotic-Labs/demo/blob/master/iotic-labs_logo600Black.png" title="Iotic-labs: Join the internet of things"></a>
</div>

Iotic-Labs
=========
Is an exciting new start-up in the IoT, based around Cambridge in the UK.  
We are a spin-off from [Arkessa] a global provider of M2M and IoT 
solutions. Our goal is to make joining the Internet of Things easy, 
safe, secure and fun.


This git-hub
----
This git-hub is our public, demo site where you'll find all the examples 
and code for the workshops and hackathons that we're running.

License
----
For this demo code we're using the [BSD] licence 


Iotic Labs demo API - Terms of use
----

These services are provided for trial, free of charge, for an unspecified
time and may be revoked or changed without notice at any time at the entire
discretion of Iotic Labs Ltd or its agents.

These services are not completely representative of our full industrial API.
Use of this software is for test and evaluation purposes only. No warranty is
provided with these services; no liability is accepted or implied that the
services are fit for use. By use of these services you acknowledge both the
above terms and that the services are used "at the user's risk" for
experimental purposes only and you further undertake to act as a good
citizen and to use the services responsibly.

By connecting to the Iotic Labs API, you agree to the above terms of use.

September 2014


What's Next?
----

Come to one of our workshops, and we'll show you how all this works. Or wait a
little while, we're putting together an instructional video that will soon be
published, that will show you how to get all this working.


Do you know what you're doing already?
----

Click on the Download as ZIP over to the right, and then uncompress this on your
Mac or Raspberry Pi or Linux PC. Windows support is not yet available, please
check back later for a later version that will soon support windows.

On your Mac, run ./setup_mac first to set up required network configuration.

On your Raspberry Pi, run ./setup_rpi first to set up required network configuration.

On your Linux PC, run ./setup_linux first to set up required network configuration.


New features in development
----

Metadata and search - this feature will allow you to register a metadata description
of your Nodes and Points and the data that they generate, and other Nodes can then
search for them via a range of different criteria. This will allow you to bind
to data points based on the type of data that they generate, rather than needing
to know their precise name in advance. This enables the design of much more
dynamic and ad-hoc systems.


Discovery - a special service that repeatedly watches for certain types of nodes
and informs your code when they come into range - this is great for building
really late-bound dynamic systems that adapt as new devices come into range
and go out of range.



[Arkessa]:http://arkessa.com
[BSD]:https://en.wikipedia.org/wiki/BSD_licenses
