#TO RUN : python -m ginipls.models.hyperparameters
import numpy as np
import traceback #for exception
import itertools # for cartesian product of params ranges
from sklearn.model_selection import KFold
import os
from ginipls.models.ginipls import PLS, PLS_VARIANT
from ginipls.config import GLOBAL_LOGGER
logger = GLOBAL_LOGGER


## DIY : sklearn.kfold + for(nu_range) + fit + score
def select_pls_hyperparameters_with_cross_val(pls_type, X, y, nu_range, n_components_range, n_folds, best_expectable_score=1.):
  """"""
  # TO SEE THE FOLDS SCORES : grep -nr '\[nu=1.700, n_comp_=5\].*score' taj-ginipls.log
  logger.debug('nu_range = %s'% str(nu_range))
  logger.debug('n_components_range =%s'% str(n_components_range))
  X = np.asarray(X) #pour kf.split(X)
  y = np.asarray(y) 
  n_folds = min(n_folds, len(X))
  logger.info("Strating a %d folds Cross-validation" % n_folds)
  kf = KFold(n_splits=n_folds, shuffle=True)
  kf.get_n_splits(X)
  best_mean_score = 0.
  best_nu_ = 0.
  best_n_comp_ = 0.
  for nu_, n_comp_  in itertools.product(nu_range, n_components_range):
    params_str = 'nu=%.3f, n_comp_=%d' % (nu_,n_comp_)
    mean_score = 0.
    fold_id = 0
    n_valid_folds = 0
    for train_index, test_index in kf.split(X):
      try:        
        logger.debug("[%s] [fold %d] TRAIN: %s, TEST: %s" % (params_str, fold_id, str(train_index), str(test_index)))
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        gpls = PLS(pls_type=pls_type, nu=nu_, n_components=n_comp_)
        gpls.fit(X_train.tolist(), y_train.tolist())
        fold_score = gpls.score(X_test.tolist(), y_test.tolist())        
        logger.debug("[%s] [fold %d] score = %.3f" % (params_str, fold_id, fold_score))
        mean_score += fold_score
      except Exception:
        tb = traceback.format_exc()
        logger.error("[%s] [fold %d] ERROR : %s" % (params_str, fold_id, tb))
      else:
        n_valid_folds += 1
      finally:
        fold_id += 1
      #break
    #mean_score = mean_score / n_valid_folds if n_valid_folds > 0 else 0.
    mean_score = mean_score / n_folds
    logger.debug("[%s] [CV n_folds_without_error=%d] mean_score = %.3f" % (params_str,n_valid_folds,mean_score))
    if best_mean_score < mean_score:
      best_mean_score = mean_score
      best_nu_ = nu_
      best_n_comp_ = n_comp_
    if best_mean_score == best_expectable_score:
      break
    #break
  logger.info("best_mean_sean_score = %.3f (with nu_==%.3f & n_comp_==%d)" % (best_mean_score, best_nu_, best_n_comp_))
  return best_nu_, best_n_comp_


if __name__ == "__main__":
  pls_type = PLS_VARIANT.GINI
  from sklearn import datasets
  iris = datasets.load_iris()
  y = iris.target[50:] # classe{2,3}
  X = iris.data[50:]
  
  X_train_sm=[[2.0, 0.0, 7.0, 4, 5.2, 9.7], [3.0, 1.0, 5.0, 4, 1.0, .97], [0.0, 4.0, 5.0, 4, .1235, 2.58], [4.0, 0.0, 7.0, 4, 10, 4.78], [4.0, 1.0, 8.0, 4, 1, 5], [1.5, 1.3, 1.1, 4, 7, 6]]
  y_train_sm=[0, 0, 0, 1, 1, 1]  
  #X = X_train_sm
  #y = y_train_sm
  
  nu_min = 1
  nu_max = 2
  nu_step = 0.1
  nu_range = [i*nu_step for i in range(int(nu_min/nu_step),int(nu_max/nu_step))]
  

  n_components_min = 1
  n_components_max = min(10,len(X[0])) # nb de caractéristiques
  n_components_step = 1
  n_components_range = range(n_components_min, n_components_max, n_components_step)

  n_folds=3
  nu, n_comp = select_pls_hyperparameters_with_cross_val(pls_type, X, y, nu_range, n_components_range, n_folds)
  logger.info("selected hyperparameters : nu=%.3f, n_comp=%d" % (nu, n_comp))
  