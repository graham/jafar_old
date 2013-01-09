//
//  GARequest.h
//  requests
//
//  Created by Graham Abbott on 12/31/12.
//  Copyright (c) 2012 Graham Abbott. All rights reserved.
//

#import <Foundation/Foundation.h>

#define GA_RETURN_DATA  0
#define GA_RETURN_STRING 1
#define GA_RETURN_JSON 2

@interface GARequest : NSObject {
    NSString *url;
    NSString *requestType;
    
    id target_delegate;
    SEL target_selector;
    NSMutableData *receivedData;
    int returnType;
    
    NSDictionary *post_args;
}

- (id)initWithURL:(NSString *)s;
- (void)postData:(NSDictionary*)d;
- (void)addDelegate:(id)d withSelector:(SEL)s;
- (void)addDelegate:(id)d withSelector:(SEL)s asString:(BOOL)asStr;
- (void)addDelegate:(id)d withSelector:(SEL)s asJSON:(BOOL)asJSON;
- (void)load;

@end
