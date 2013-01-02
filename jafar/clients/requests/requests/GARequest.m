//
//  GARequest.m
//  requests
//
//  Created by Graham Abbott on 12/31/12.
//  Copyright (c) 2012 Graham Abbott. All rights reserved.
//

#import "GARequest.h"

@implementation GARequest

- (id)init {
    if (self = [super init]) {
        // build the object
        requestType = @"GET";
    }
    return self;
}

- (id)initWithURL:(NSString *)s {
    if (self = [self init]) {
        url = [s copy];
    }
    return self;
}

- (void)addDelegate:(id)d withSelector:(SEL)s {
    target_delegate = d;
    target_selector = s;
    returnType = GA_RETURN_DATA;
}

-(void)addDelegate:(id)d withSelector:(SEL)s asString:(BOOL)asStr {
    target_delegate = d;
    target_selector = s;
    returnType = GA_RETURN_STRING;
}

-(void)addDelegate:(id)d withSelector:(SEL)s asJSON:(BOOL)asJSON {
    target_delegate = d;
    target_selector = s;
    returnType = GA_RETURN_JSON;
}

-(void)load {
    NSMutableURLRequest *theRequest = [NSMutableURLRequest
                                        requestWithURL:[NSURL URLWithString:url]
                                        cachePolicy:NSURLRequestUseProtocolCachePolicy
                                        timeoutInterval:60.0f * 3];
    [theRequest setHTTPMethod:requestType];
    NSLog(@"Conn %@", [[NSURLConnection alloc]
                       initWithRequest:theRequest
                       delegate:self]);
}

- (void)connection:(NSURLConnection *)connection didReceiveResponse:(NSURLResponse *)response {
    receivedData = [[NSMutableData alloc] init];
}

- (void)connection:(NSURLConnection *)connection didReceiveData:(NSData *)data {
    [receivedData appendData:data];
}

- (void)connection:(NSURLConnection *)connection didFailWithError:(NSError *)error {
    NSLog(@"Connection failed! Error %@ - %@",
		  url,
          [error localizedDescription]);
}

- (void)connectionDidFinishLoading:(NSURLConnection *)connection {
    @try {
        NSError *e = nil;
        NSMethodSignature * sig = nil;
        id arg = nil;

        sig = [[target_delegate class]
                instanceMethodSignatureForSelector:target_selector];
        
        NSInvocation * myInvocation = nil;
        
        if (sig == nil) {
            NSLog(@"Tried to call a function that doesn't seem to exists, %@",
                  target_delegate);
            return;
        } else {
            myInvocation = [NSInvocation invocationWithMethodSignature:sig];
            [myInvocation setTarget:target_delegate];
            [myInvocation setSelector:target_selector];

            [myInvocation setArgument:&url atIndex:2];

            if (returnType == GA_RETURN_DATA) {
                [myInvocation setArgument:&receivedData atIndex:3];
            } else if (returnType == GA_RETURN_STRING) {
                arg = [[NSString alloc] initWithData:receivedData
                                                    encoding:NSUTF8StringEncoding];
                [myInvocation setArgument:&arg atIndex:3];
            } else if (returnType == GA_RETURN_JSON) {
                arg = [NSJSONSerialization JSONObjectWithData:receivedData options:0 error:&e];
                [myInvocation setArgument:&arg atIndex:3];
            }
            [myInvocation retainArguments];
            [myInvocation invoke];
        }
    }
    
    @catch (NSException * e) {
        NSLog(@"CALLBACK ERROR: %@", e);
        return;
    }
    
    @finally {
        
    }
    return;
}

@end
