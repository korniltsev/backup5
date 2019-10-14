use lib 'lib';
use lib 'lib/session/';
use Hourglass;
use Hourglass::Session;
use Plack::Builder;

my $app = Hourglass->new();
builder{
    $app->run;
}
