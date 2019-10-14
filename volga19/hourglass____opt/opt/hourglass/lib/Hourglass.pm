package Hourglass;
use strict;
use Kelp::Base 'Kelp';
use Plack::Middleware::Session::SerializedCookie;
use Data::Dumper;
use DBI;
use utf8;
use Crypt::Argon2 qw(argon2id_pass argon2id_verify);
use Crypt::URandom qw(urandom);
use HTML::Entities qw(encode_entities);
use Regexp::Common qw( number );


my $secret = "ti6EeSaChaengooCipij4eiw7Bah4anaivujooRe";

my $dbh = DBI->connect(
    "dbi:mysql:database=hourglass;host=127.0.0.1;port=3306",
    'hourglass',
    'hourglass',
    { RaiseError => 1, PrintError => 0, mysql_enable_utf8 => 1 });

my @statements = map { $dbh->prepare($_) } (
    "SELECT id,username,password FROM user WHERE username = ?",
    "INSERT INTO user(username,password) VALUES (?,?)",
    "SELECT username FROM user WHERE id=?",
    "SELECT w.title as title, w.time as time, p.name as project FROM worklog w LEFT JOIN project p on w.project_id = p.id WHERE w.user_id=? ORDER BY w.creation_date DESC LIMIT 10;",
    "INSERT INTO project(user_id, name) VALUES(?,?)",
    "INSERT INTO worklog(user_id, title, project_id, time) VALUES(?,?,?,?)",
    "SELECT id, name FROM project WHERE user_id=?",
    "SELECT p.name as name, SUM(time) as sum FROM worklog w LEFT JOIN project p on w.project_id = p.id WHERE w.user_id = ? GROUP BY p.name;",
    "SELECT id from project where name = ? and user_id=?"
);

sub run {
    my $self = shift;
    my $app = $self->SUPER::run(@_);
    my $session_serializer = Hourglass::Session->new($secret);
    $app = Plack::Middleware::Session::SerializedCookie->wrap($app, (
        serializer => $session_serializer,
        path  => "/",
        httponly => "true",
        serialize_exception => sub { my $error_msg = shift; print $error_msg . "\n"; return {}},
        deserialize_exception => sub { my $error_msg = shift; print $error_msg . "\n"; return {}},
    ));
    return $app;
}

sub build {
    my $self = shift;
    my $r    = $self->routes;
    $r->add('/login', sub { 
        my $self = shift;        
        $self->template('login');
    });
    
    $r->add('/', sub {
        my $self = shift;
	    my $user_id = $self->req->session('user_id');
	    if(defined($user_id)){
            return $self->res->redirect_to('/home/index');
	    }   
	    else{
	        return $self->res->redirect_to('/login');
	    }
    });

    $r->add([POST => '/login'], 'do_login');
    $r->add('/logout', 'logout');
    $r->add( '/home', {to => 'check_auth', bridge=>1});
    $r->add( '/home/index', 'home');
    $r->add( '/home/project', sub {
        my $self = shift;
        $self->template('project');
    });
    $r->add([POST => '/home/project'], 'do_create_project');
    $r->add('/home/worklog', sub {
        my $self = shift;
        $statements[6]->execute($self->req->session('user_id'));
        my $projects = $statements[6]->fetchall_arrayref();
        my @projects_data = ();
        foreach my $project (@$projects){
            my @project_arr = @$project;
            push @projects_data, {id => $project_arr[0], name => encode_entities($project_arr[1])};
        }
        $self->template('worklog', {projects => \@projects_data});
    });
    $r->add([POST => '/home/worklog'], 'do_create_worklog');
    $r->add('/home/import', sub {
        my $self = shift;
        $self->template('import');
    });
    $r->add([POST => '/home/import'], 'do_import');
    $r->add('/home/report', 'report');
    $r->add([GET => '/home/import/debug'], 'debug_import');
    $r->add( '/config', sub { $_[0]->config_hash } );
}

sub home {
    my $self = shift;
    my $user_id = $self->req->session('user_id');
    $statements[2]->execute($user_id) or die "Cannot execute statement";
    my $username = $statements[2]->fetchrow_hashref()->{'username'};
    $statements[3]->execute($user_id) or die "Cannot execute statement";
    my $worklog = $statements[3]->rows > 0 ? $statements[3]->fetchall_arrayref() : ();
    my @worklog_data = ();
    foreach my $row (@$worklog){
        my @row_arr = @$row;
        push @worklog_data, 
        {title => encode_entities($row_arr[0]), project => encode_entities(defined($row_arr[2]) ? $row_arr[2] : ""), time => encode_entities($row_arr[1])};
    }        
    $self->template('home', {username => encode_entities($username), worklog => \@worklog_data});
}

sub logout {
    my $self = shift;
    $self->req->session( {} );
    return $self->res->redirect_to('/login');
}

sub check_auth {
    my $self = shift;
    my $user_id = $self->req->session('user_id');
    if(defined($user_id)){
        return 1;
    }
    else{
        return 0;
    }
}

sub do_import {
    my $self = shift;
    my $uploads = $self->req->uploads;
    my $import_file = $uploads->{'import_file'};
    my $import_file_name = $import_file->{'tempname'};
    open(TMP_CSV, $import_file_name) or die "Cannot process file";
    my $i = 0;
    my @csv_records = ();
    while (my $record = <TMP_CSV>){
        if($i > 10){
            break;
        }
        my @strings = split(/,/, $record);
        my $title = $strings[0];
        chomp($title);
        my $project = $strings[1];
        chomp($project);
        my $time = $strings[2];
        chomp($time);
        push @csv_records, {title => $title, project =>$project , time => $time};
        $i++;
    }
    close(TMP_CSV);
    dump_file($import_file, \@csv_records);
    my $user_id = $self->req->session('user_id');
    save_records(\@csv_records, $user_id);
    return $self->res->redirect_to('/home/index');
}

sub save_records {
    my $records = shift;
    my $user_id = shift;
    foreach my $record (@$records){
        my $project_id;
        $statements[8]->execute($record->{project}, $user_id) or die "Cannot execute statement!";
        if($statements[8]->rows > 0){
            $project_id = $statements[8]->fetchrow_hashref->{id};            
        }
        elsif(defined($record->{project})){
            $statements[4]->execute($user_id, $record->{project}) or die "Cannot execute statement!";
            $project_id = $dbh->{'mysql_insertid'};        
        }

        if(defined($record->{title}) && defined($record->{time}) && $record->{time} =~ /$RE{num}{int}/ && abs($record->{time}) == $record->{time}){
            $project_id = $project_id if $project_id =~ /$RE{num}{int}/ && abs($project_id) == $project_id;
            $statements[5]->execute($user_id, $record->{title}, $project_id, $record->{time}) or die "Cannot create statement";        
        }        
    }
}

sub do_create_project {
    my $self = shift;
    my $project = $self->param('project');
    if(defined($project)){
        my $user_id = $self->req->session('user_id');
        $statements[4]->execute($user_id, $project) or die "Cannot execute statement";    
        return $self->res->redirect_to('/home/index');
    }
    else{
        return $self->res->redirect_to('/home/project');
    }
}

sub do_create_worklog {
    my $self = shift;
    my $title = $self->param('title');
    my $time = $self->param('time');
    my $project = $self->param('project');

    if(defined($title) && defined($time) && $time =~ /$RE{num}{int}/ && abs($time) == $time){
        my $project_id = $project if $project =~ /$RE{num}{int}/ && abs($project) == $project;
        my $user_id = $self->req->session('user_id');
        $statements[5]->execute($user_id, $title, $project_id, $time) or die "Cannot create statement";
        return $self->res->redirect_to('/home/index');
    }
    else{
        return $self->res->redirect_to('/home/worklog');
    }

}

sub dump_file {
    my $uploads = shift;
    my @contents = shift;
    my $filename = $uploads->{filename};
    open(DATA_FILE, ">./import_data/$filename") or die "Cannot open file!";
    print DATA_FILE Dumper(@contents);
    close(DATA_FILE);
}

sub debug_import {
    my $self = shift;
    my $filename = $self->param('filename');
    open(DATA_FILE, "./import_data/$filename") or die "Cannot open file!";
    read DATA_FILE, my $file_content, -s DATA_FILE;
    close(DATA_FILE);
    $self->res->text->render($file_content);
}

sub report {
    my $self = shift;
    my $user_id = $self->session->{user_id};
    $statements[7]->execute($user_id) or die "Cannot execute statement";
    my $report = $statements[7]->rows > 0 ? $statements[7]->fetchall_arrayref() : ();
    my @report_data = ();
    foreach my $row (@$report){
        my @row_arr = @$row;
        push @report_data, {name => encode_entities(defined($row_arr[0]) ? $row_arr[0] : "Without projects"), sum => encode_entities($row_arr[1])};
    }
    return $self->template('report', {report => \@report_data});
}

sub do_login {
    my $self = shift;
    my $username = $self->param('username');
    my $password = $self->param('password');
    if(defined($username) && defined($password)){    
        $statements[0]->execute($username) or die "Failed to execute statement $dbh->errstr()";
        if($statements[0]->rows > 0){
            my $user_record = $statements[0]->fetchrow_hashref();
            if(argon2id_verify($user_record->{'password'}, $password)){
                $self->req->session->{user_id} = $user_record->{'id'};
                return $self->res->redirect_to('/home/index');
            }
            return $self->res->redirect_to('/login');
        }
        else{
            if($username =~ m/[^a-zA-Z0-9]/){
                return $self->res->redirect_to('/login');            
            }
            else{
                my $salt = urandom(16);
                my $encoded_password = argon2id_pass($password, $salt, 3, '32M', 1 , 16);
                $statements[1]->execute($username, $encoded_password) or die "Failed to execute statement $dbh->errstr()";
                my $insertid = $dbh->{'mysql_insertid'};
                $self->req->session->{user_id} = $insertid;
                return $self->res->redirect_to('/home/index');
            }
        }
    }
    else{
        return $self->res->redirect_to('/login');
    }
}

1;
