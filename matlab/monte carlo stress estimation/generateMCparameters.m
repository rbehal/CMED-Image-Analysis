function [generatedParameterArray] = generateMCparameters(errorType, params, varargin)
    assert(isvector(params) & isnumeric(params) & length(params)>1,'parameter input must be a vector of at least 2 entries (see documentation)')

    p = inputParser();
    p.addParameter('numSamples', 100000, ...
        @(x) isnumeric(x) && isscalar(x) && x>100);
    p.addParameter('plot', false, ...
                   @islogical);
    
    MonteCarlo_length = varargin{:};
    generatedParameterArray = zeros(1,MonteCarlo_length);
    
    %fprintf('Montecarlo sampling: %3.0f%%\n',0);
    
    switch(errorType)
        case 'gaussian'     % gaussian errors
            assert(isvector(params) & length(params)==2 & isnumeric(params),'please give parameters in the following way: [x,dx]')
            for idx = 1:100
                for kdx = 1:ceil(MonteCarlo_length/100)
                    parameterIDX = (idx-1)*ceil(MonteCarlo_length/100)+kdx;
                    generatedParameterArray(parameterIDX) = normrnd(params(1), params(2));
                end
                %fprintf('\b\b\b\b\b%3.0f%%\n',idx);
            end
        case 'binomial'     % binomial errors
            assert(isvector(params) & length(params)==2 & isnumeric(params) & params(1)>=params(2) & sum(floor(params)==params)==2,'please give parameters in the following way: [n,k]')
            assert(params(1)<1001,'n cannot be larger than 1000 (need to use possion)')
                    
            n = params(1);
            k = params(2);
            prop = k/n;
            kvec = 0:n;
            binomialKoeff=binomial(n,kvec);
            binomialDist = binomialKoeff.*prop.^kvec.*(1-prop).^(n-kvec);
            binomialDistCumSum = cumsum(binomialDist);
            binomialDistCumSum(end+1) = 2;
            normalDistRandomNumbers = rand(1,MonteCarlo_length);

            Axis=0:length(binomialDist);
            [~,indx] = histc(normalDistRandomNumbers,binomialDistCumSum); 
            binomialDistRandomNumbers = Axis(indx(1:end)+1);
            generatedParameterArray = binomialDistRandomNumbers./n;
            %fprintf('\b\b\b\b\b%3.0f%%\n',100);
            
        case 'bootstrapDistribution'    % bootstrap from measured values
            assert(isvector(params) & length(params)>=5 & isnumeric(params),'please give parameters in the following way: [x1,x2,x3,...,xn]')
            generatedParameterArray = params((randsample(length(params),MonteCarlo_length,true)));
            fprintf('\b\b\b\b\b%3.0f%%\n',100);
        case 'bootstrapMean'
            assert(isvector(params) & length(params)>=5 & isnumeric(params),'please give parameters in the following way: [x1,x2,x3,...,xn]')
            for idx = 1:100
                for kdx = 1:ceil(MonteCarlo_length/100)
                    parameterIDX = (idx-1)*ceil(MonteCarlo_length/100)+kdx;
                    generatedParameterArray(parameterIDX) = mean(params((randsample(length(params),length(params),true))));
                end
                fprintf('\b\b\b\b\b%3.0f%%\n',idx);
            end
        otherwise
            error('errorType must be either: gaussian, binomial, bootstrapDistribution, or bootstrapMean');
    end
    
end