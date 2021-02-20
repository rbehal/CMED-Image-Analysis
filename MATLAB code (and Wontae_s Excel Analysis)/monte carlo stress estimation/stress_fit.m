%========================================================================
%Name: Microspherical stress gauge (MSG) 3D model data calibration fit
%Author: Nik Kalashnikov
%========================================================================
%% Initializations.
clear
clc
%Import parametric sweep data from COMSOL.
fileID=fopen('data.txt','r');
formatSpec='%f %f %f %f';
sizeA=[4 Inf];
A=fscanf(fileID,formatSpec,sizeA);
fclose(fileID);
A=A';
%Restructure data.
x=reshape(A(:,1),41,41)';
y=reshape(A(:,2),41,41)';
axial=reshape(A(:,3),41,41)';
radial=reshape(A(:,4),41,41)';

%% Fitting.
%Axial stress interpolation fit.
[xData1,yData1,zData1]=prepareSurfaceData(x,y,axial);
ft1='linearinterp';
[fitresult1,gof1]=fit([xData1,yData1],zData1,ft1,'Normalize','on');
%Radial stress interpolation fit.
[xData2,yData2,zData2]=prepareSurfaceData(x,y,radial);
ft2='linearinterp';
[fitresult2,gof2]=fit([xData2,yData2],zData2,ft1,'Normalize','on');

%% Process data.
%Process bead deformation data (axial, radial, std axial, std radial) for
%stress results (axial, CI_low_a, CI_high_a, radial, CI_low_r, CI_high_r).
%Number of Monte Carlo samples.
n=input(['Please input number of Monte Carlo samples to run1' ... 
        'for error propagation:\n']);
%Read experimental data.
fileID1=fopen('exp_data.txt','r');
formatSpec1='%f %f %f %f';
sizeA1=[4 Inf];
A1=fscanf(fileID1,formatSpec1,sizeA1);
fclose(fileID1);
A1=A1';
disp('Input strains:');
disp(A1);
%Axial stress from interpolation.
stress_axial=fitresult1(A1(:,1),A1(:,2));
%Radial stress from interpolation.
stress_radial=fitresult2(A1(:,1),A1(:,2));
disp('Output stresses from interpolation:');
disp([stress_axial stress_radial])
%Write text.
fileID2=fopen('result_data.txt','w');
%Monte Carlo error propagation.
for i=1:size(A1(:,1))
    I1=generateMCparameters('gaussian',[A1(i,1),A1(i,3)],n);
    I2=generateMCparameters('gaussian',[A1(i,2),A1(i,4)],n); 
    paramMatrix=[I1;I2];
    [funValue,funCI,funSamples]=propagateErrorWithMC(fitresult1,paramMatrix);
    means_a(i,1)=funValue;
    error_a(i,:)=funCI;
    [funValue,funCI,funSamples]=propagateErrorWithMC(fitresult2,paramMatrix);
    means_r(i,1)=funValue;
    error_r(i,:)=funCI;
    results(i,:)=[means_a(i,:),error_a(i,:),means_r(i,:),error_r(i,:)];
    fprintf(fileID2,'%f %f %f %f %f %f\r\n',results(i,1),results(i,2),results(i,3),results(i,4),results(i,5),results(i,6));
end
disp('Output stresses with errors using Monte Carlo:');
disp(results);
%Close text.
fclose(fileID2);