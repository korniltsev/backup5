package Hourglass::Session;
use strict;
use JSON;
use MIME::Base64 qw(encode_base64url decode_base64url);
use Try::Tiny;
use Digest::SHA qw(hmac_sha1 hmac_sha1_hex);
use Data::Dumper;
use Encode qw(encode decode_utf8);
use Magic::Key;
use utf8;

sub new{
    my $class = shift;
    my $self = {
        _secret => shift  
    };
    bless $self, $class;
    print "SECRET $self->{_secret}\n";
    my $key = Magic::Key::derive_key($self->{_secret});
    $self->{_key} = $key;
    return $self;
}

sub serialize(){
    my $self = shift;
    my $session_hash = shift;
    try{
        my $json_string = JSON->new->utf8->encode($session_hash);    
        my $digest = hmac_sha1_hex($json_string, $self->{_key});
        return encode_base64url($json_string) . "." . encode_base64url($digest);
    }
    catch{
        print "Error: $_";
        return "";
    }
    
}

sub deserialize(){
    my $self = shift;
    my $session_value = shift;
    try{
        my @session_fields = split(/\./, $session_value);    
        my $session = $session_fields[0];    
        my $digest = decode_base64url($session_fields[1]);        
        my $json = decode_base64url($session);
        unless(hmac_sha1_hex($json, $self->{_key}) eq $digest){
            return {}
        }
        return JSON->new->utf8->decode(decode_utf8($json) or die "Failed to encode UTF8 value");
    }
    catch{
        print "Error: $_";
        return {};
    }
}



1;
__END__
